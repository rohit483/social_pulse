# Copyright (C) 2026 ROHIT CHAWDA
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.

import os
import logging

# --- Bootstrapping: Auto-extract sessions from cookie.json if provided (Dev Only) ---
if os.path.exists("cookie.json") and os.path.getsize("cookie.json") > 10:
    print("Running session extraction from cookie.json...")
    try:
        from extract_sessions import generate_from_json
        generate_from_json()
    except Exception as e:
        print(f"Warning: Session extraction failed: {e}")

import time
import pandas as pd
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

# Import modules
from modules import process_csv_sentiment, InstagramScraper, Config 
from modules.database.models import db, InstagramScrape, InstagramComment, CsvUpload, CsvComment
from functools import wraps

#=======================================    App    =======================================
# Initialize App
app = Flask(__name__)
Config.init_app(app)
app.config['SQLALCHEMY_DATABASE_URI'] = Config.SQLALCHEMY_DATABASE_URI
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = Config.SQLALCHEMY_TRACK_MODIFICATIONS
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
db.init_app(app)
with app.app_context():
    db.create_all()

# Restrict CORS to known origins (configurable via ALLOWED_ORIGINS in .env)
CORS(app, origins=os.environ.get('ALLOWED_ORIGINS', 'http://localhost,http://localhost:5000').split(','))

# Rate limiter - use Redis in production if REDIS_URL is set, else fall back to memory
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],  # No global limit; apply per-route
    storage_uri=os.environ.get('REDIS_URL', 'memory://')
)

# Global Scraper Placeholder
scraper = None

#=======================================    Helper Functions    =======================================
# Function to load instagram scraper instance
def get_scraper():
    global scraper
    if scraper is None:
        try:
            scraper = InstagramScraper()
            if scraper.instaloader_active or scraper.instagrapi_active:
                logging.info("InstagramScraper initialized successfully.")
            else:
                logging.warning("InstagramScraper initialized but NO active sessions found.")
        except Exception as e:
            logging.error(f"Failed to initialize global scraper: {e}")
            return None
    return scraper

#------------------------------------------------------------------------------------------
# Global Error Handler
@app.errorhandler(Exception)
def handle_exception(e):
    from werkzeug.exceptions import NotFound
    if isinstance(e, NotFound):
        return jsonify({"error": "Not Found"}), 404
        
    logging.error(f"Global Error: {e}", exc_info=True)
    # Return generic JSON for errors
    return jsonify({"error": "An internal server error occurred."}), 500

#=======================================    Routes    =======================================
# --- 1. Home Routes ---
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/privacy-policy')
def privacy_policy():
    return render_template('privacy-policy.html')

@app.route('/terms')
def terms():
    return render_template('terms.html')

@app.route('/license')
def license_page():
    try:
        with open('LICENSE', 'r') as f:
            return Response(f.read(), mimetype='text/plain')
    except Exception as e:
        return jsonify({"error": "License file not found."}), 404

#-----------------------------------------------------------------------------------
# --- 2. Sentiment Analysis Routes ---
@app.route('/analyze_upload', methods=['POST'])
@limiter.limit("30 per minute")
def analyze_upload(): 
    if 'file' not in request.files:
         return jsonify({"error": "No file part"}), 400     

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.csv'):
        filename = secure_filename(file.filename)
        filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
        file.save(filepath)

        counts, comments, error = process_csv_sentiment(filepath)
        
        if error:
            return jsonify({"error": error}), 500
            
        # Save to database
        try:
            upload_job = CsvUpload(filename=filename)
            db.session.add(upload_job)
            db.session.flush()
            for c in comments:
                db.session.add(CsvComment(
                    upload_id=upload_job.id, 
                    username=c.get('username', 'unknown'), 
                    text=c.get('comment', ''), 
                    sentiment=c.get('sentiment', 'N/A')
                ))
            db.session.commit()
            logging.info(f"Saved CSV upload {filename} to database with ID {upload_job.id}")
        except Exception as db_err:
            logging.error(f"Failed to save CSV to DB: {db_err}")
            db.session.rollback()
            
        return jsonify({
            "counts": counts,
            "comments": comments,
            "filename": filename
        })
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV."}), 400

#-----------------------------------------------------------------------------------
# --- 3. Instagram Scraping Routes ---
@app.route('/scrape', methods=['POST'])
@limiter.limit("10 per minute")
def scrape_comments_route():
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    shortcode = data.get('shortcode')

    import re
    # Validate shortcode format and length
    if not shortcode or not isinstance(shortcode, str) or not re.match(r'^[a-zA-Z0-9_-]{1,30}$', shortcode):
        return jsonify({"error": "Invalid shortcode format"}), 400

    scraper_service = get_scraper()
    if not scraper_service:
        return jsonify({"error": "Scraper service unavailable"}), 503

    # Check session health - if both inactive, try refresh
    if not scraper_service.instagrapi_active and not scraper_service.instaloader_active:
        logging.warning("Sessions inactive before scrape. Attempting refresh...")
        scraper_service.setup_session()
        
        if not scraper_service.instagrapi_active and not scraper_service.instaloader_active:
            return jsonify({
                "error": "No active sessions available. Please refresh sessions manually via /admin/refresh-session"
            }), 503

    try:
        comments = scraper_service.scrape_comments(shortcode)
    except Exception as e:
        logging.error(f"Scraping failed: {e}")
        return jsonify({"error": f"Scraping failed: {str(e)}"}), 500
    
    # Perform Sentiment Analysis immediately
    df_temp = pd.DataFrame(comments)
    sentiment_counts = {}
    analyzed_comments = comments

    if not df_temp.empty and 'comment' in df_temp.columns:
            from modules.analysis.sentiment import analyze_sentiment_text
            df_temp['sentiment'] = df_temp['comment'].apply(analyze_sentiment_text)
            analyzed_comments = df_temp.to_dict(orient='records')
            sentiment_counts = df_temp['sentiment'].value_counts().to_dict()
            
    # Save to database
    try:
        scrape_job = InstagramScrape(shortcode=shortcode)
        db.session.add(scrape_job)
        db.session.flush()
        for c in analyzed_comments:
            db.session.add(InstagramComment(
                scrape_id=scrape_job.id, 
                username=c.get('username', 'unknown'), 
                text=c.get('comment', ''), 
                sentiment=c.get('sentiment', 'N/A')
            ))
        db.session.commit()
        logging.info(f"Saved scrape for {shortcode} to database with ID {scrape_job.id}")
    except Exception as db_err:
        logging.error(f"Failed to save scrape to DB: {db_err}")
        db.session.rollback()

    return jsonify({
        "comments": comments,
        "analyzed_comments": analyzed_comments,
        "sentiment_counts": sentiment_counts
    })

#-----------------------------------------------------------------------------------
# --- 4. Download Raw CSV Routes ---
@app.route('/download_csv', methods=['POST'])
def download_csv_route(): 
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    comments = data.get('comments')
    shortcode = data.get('shortcode', 'post')

    if not isinstance(comments, list) or not comments:
        return jsonify({"error": "Invalid or empty 'comments' list"}), 400
        
    # Use Pandas for CSV Generation
    df = pd.DataFrame(comments)
    # Ensure correct column order/naming if needed, or just dump as is
    
    return Response(
        df.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename=Raw_Instagram_Comments_{shortcode}.csv"}
    )

#-----------------------------------------------------------------------------------
# --- 5. Download Analyzed CSV Routes ---
@app.route('/download_analyzed_csv', methods=['POST'])
def download_analyzed_csv_route(): 
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    comments = data.get('comments') 
    # Sanitize filename_prefix
    import re
    raw_prefix = data.get('filename_prefix', 'analyzed_data')
    filename_prefix = re.sub(r'[^a-zA-Z0-9_\-]', '_', raw_prefix)[:50]

    if not isinstance(comments, list) or not comments:
        return jsonify({"error": "Invalid or empty 'comments' list"}), 400
        
    saved_filename = f"{filename_prefix}_{int(time.time())}.csv"
    save_path = os.path.join(Config.DOWNLOAD_FOLDER, saved_filename)
    
    # Use Pandas for CSV Generation & Saving
    df = pd.DataFrame(comments)
    
    # Save to disk
    df.to_csv(save_path, index=False, encoding='utf-8')
    
    # Return download response
    return Response(
        df.to_csv(index=False),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment;filename={saved_filename}"}
    )

#=======================================    Admin Security    =======================================
def require_admin_token(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = request.headers.get('X-Admin-Token') or request.args.get('X-Admin-Token', '')
        if not token or token != Config.SECRET_KEY:
            return jsonify({"error": "Unauthorized"}), 401
        return f(*args, **kwargs)
    return decorated

#-----------------------------------------------------------------------------------
# --- 6. Admin Session Management Routes ---
@app.route('/admin/check-session', methods=['GET'])
@require_admin_token
def check_session():
    """Check if sessions are active and healthy"""
    scraper_service = get_scraper()
    if not scraper_service:
        return jsonify({
            "status": "error",
            "message": "Scraper not initialized"
        }), 503
    
    return jsonify({
        "status": "ok",
        "instagrapi_active": scraper_service.instagrapi_active,
        "instaloader_active": scraper_service.instaloader_active,
        "message": "Session check complete"
    })

#-----------------------------------------------------------------------------------
@app.route('/admin/refresh-session', methods=['POST'])
@require_admin_token
def refresh_session():
    """Manually trigger session refresh/re-initialization"""
    global scraper
    
    logging.info("Manual session refresh triggered by admin...")
    
    try:
        # Force re-initialization
        scraper = None
        scraper_service = get_scraper()
        
        if scraper_service and (scraper_service.instagrapi_active or scraper_service.instaloader_active):
            return jsonify({
                "status": "success",
                "message": "Session refreshed successfully",
                "instagrapi_active": scraper_service.instagrapi_active,
                "instaloader_active": scraper_service.instaloader_active
            })
        else:
            return jsonify({
                "status": "partial",
                "message": "Session refresh attempted but no active sessions",
                "instagrapi_active": False,
                "instaloader_active": False
            }), 503
            
    except Exception as e:
        logging.error(f"Session refresh failed: {e}")
        return jsonify({
            "status": "error",
            "message": str(e)
        }), 500

#============================================   Main   =======================================
if __name__ == '__main__':
    # Read debug mode from env
    debug_mode = os.environ.get('FLASK_DEBUG', '0') == '1'
    app.run(host='0.0.0.0', port=5000, debug=debug_mode)