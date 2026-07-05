import os
import time
import pandas as pd
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from werkzeug.utils import secure_filename

# Import modules
from modules import process_csv_sentiment, InstagramScraper, Config 
from functools import wraps

#=======================================    App    =======================================
# Initialize App
app = Flask(__name__)
Config.init_app(app)
CORS(app)

# Rate limiter - keyed by remote IP
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=[],  # No global limit; apply per-route
    storage_uri="memory://"
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
        
    logging.error(f"Global Error: {e}")
    # Return JSON instead of HTML for API errors
    return jsonify({"error": str(e)}), 500

#=======================================    Routes    =======================================
# --- 1. Home Routes ---
@app.route('/')
def home():
    return render_template('index.html')

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

    if not shortcode:
        return jsonify({"error": "Missing 'shortcode'"}), 400

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
        headers={"Content-Disposition": f"attachment;filename=instagram_comments_{shortcode}.csv"}
    )

#-----------------------------------------------------------------------------------
# --- 5. Download Analyzed CSV Routes ---
@app.route('/download_analyzed_csv', methods=['POST'])
def download_analyzed_csv_route(): 
    if not request.is_json:
        return jsonify({"error": "Request must be JSON"}), 400

    data = request.get_json()
    comments = data.get('comments') 
    filename_prefix = data.get('filename_prefix', 'analyzed_data')

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
        token = request.headers.get('X-Admin-Token', '')
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
    app.run(host='0.0.0.0', port=5000, debug=True)