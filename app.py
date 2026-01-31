import os
import time
import pandas as pd
import logging
from flask import Flask, render_template, request, jsonify, redirect, url_for, Response
from flask_cors import CORS
from werkzeug.utils import secure_filename

# Import modules
from modules import process_csv_sentiment, InstagramScraper, Config 

#=======================================    App    =======================================
# Initialize App
app = Flask(__name__)
Config.init_app(app)
CORS(app)

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

    comments = scraper_service.scrape_comments(shortcode)
    
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

#============================================   Main   =======================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)