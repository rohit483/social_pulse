import os
import csv
import io
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
# 1. Function to load instagram scraper instance
def get_scraper():
    global scraper
    if scraper is None:
        try:
            scraper = InstagramScraper()
            logging.info("InstagramScraper initialized successfully.")
        except Exception as e:
            logging.error(f"Failed to initialize global scraper: {e}")
            return None
    return scraper

#-----------------------------------------------------------------------------------
# 2. Function to generate CSV response
def generate_csv_response(data_list, headers, filename, save_path=None):
    try:
        output = io.StringIO()
        writer = csv.writer(output, quoting=csv.QUOTE_ALL)
        
        # Write Header
        writer.writerow(headers)
        # Write Rows
        keys = [h.lower() for h in headers]
        
        # Write Data
        for item in data_list:
            row = [item.get(key, '') for key in keys]
            writer.writerow(row)
            
        # Get CSV Content
        csv_content = output.getvalue()
        output.seek(0)
        
        # Optionally save to disk
        if save_path:
            with open(save_path, 'w', newline='', encoding='utf-8') as f:
                f.write(csv_content)
                
        # Return Response
        return Response(
            csv_content, 
            mimetype="text/csv", 
            headers={"Content-Disposition": f"attachment;filename={filename}"}
        )
    except Exception as e: # Exception Handling
        logging.error(f"CSV Generation Error: {e}")
        return jsonify({"error": f"Failed to generate CSV: {str(e)}"}), 500

#=======================================    Routes    =======================================
# --- 1. Home Routes ---
@app.route('/')
def home():
    return render_template('index.html')

#-----------------------------------------------------------------------------------
# --- 2. Sentiment Analysis Routes ---
@app.route('/analyze_upload', methods=['POST'])
# Handle CSV upload and sentiment analysis. Expected input as CSV file
def analyze_upload(): 
    if 'file' not in request.files: # Check if file is in the request
         return jsonify({"error": "No file part"}), 400     

    file = request.files['file'] # Get the file from the request

    # Check if the file is empty
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    # Check if the file is a CSV    
    if file and file.filename.endswith('.csv'):
        try:
            filename = secure_filename(file.filename)
            filepath = os.path.join(Config.UPLOAD_FOLDER, filename)
            file.save(filepath)

            # Analyze the uploaded CSV
            counts, comments, error = process_csv_sentiment(filepath)
            
            # Return error if any
            if error:
                return jsonify({"error": error}), 500
                
            # Return counts, comments and filename
            return jsonify({
                "counts": counts,
                "comments": comments,
                "filename": filename
            })

        # Exception Handling    
        except Exception as e:
             return jsonify({"error": f"Analysis failed: {str(e)}"}), 500

    # Invalid file type         
    else:
        return jsonify({"error": "Invalid file type. Please upload a CSV."}), 400

#-----------------------------------------------------------------------------------
# --- 3. Instagram Scraping Routes ---
@app.route('/scrape', methods=['POST'])
# Handle Instagram scraping. Expected input as JSON with 'shortcode' key
def scrape_comments_route():
    if not request.is_json: # Check if request is JSON
        return jsonify({"error": "Request must be JSON"}), 400

    # Get JSON data from request
    data = request.get_json()

    # Get shortcode from JSON data
    shortcode = data.get('shortcode')

    # Check if shortcode is present
    if not shortcode:
        return jsonify({"error": "Missing 'shortcode'"}), 400

    # Get Scraper Instance (Lazy Load)
    scraper_service = get_scraper()
    if not scraper_service:
        return jsonify({"error": "Scraper service unavailable"}), 503

    try:
        # Perform Scraping
        comments = scraper_service.scrape_comments(shortcode)
        
        # Perform Sentiment Analysis immediately
        df_temp = pd.DataFrame(comments)
        
        # nitialize sentiment counts
        sentiment_counts = {}
        analyzed_comments = comments # Default to raw if analysis fails/empty

        # Perform Sentiment Analysis
        if not df_temp.empty and 'comment' in df_temp.columns:
             from modules.analysis.sentiment import analyze_sentiment_text
             
             # Apply analysis
             df_temp['sentiment'] = df_temp['comment'].apply(analyze_sentiment_text)
             
             # Convert back to dict
             analyzed_comments = df_temp.to_dict(orient='records')
             sentiment_counts = df_temp['sentiment'].value_counts().to_dict()

        # Return comments, analyzed comments and sentiment counts
        return jsonify({
            "comments": comments, # Raw data
            "analyzed_comments": analyzed_comments,
            "sentiment_counts": sentiment_counts
        })

    # Exception Handling    
    except Exception as e:
        return jsonify({"error": str(e)}), 500

#-----------------------------------------------------------------------------------
# --- 4. Download Raw CSV Routes ---
@app.route('/download_csv', methods=['POST'])
# Handle Raw CSV download. Expected input as JSON with 'comments' key
def download_csv_route(): 
    if not request.is_json: # Check if request is JSON
        return jsonify({"error": "Request must be JSON"}), 400

    # Get JSON data from request
    data = request.get_json()
    comments = data.get('comments')
    shortcode = data.get('shortcode', 'post')

    # Validate input
    if not isinstance(comments, list) or not comments:
        return jsonify({"error": "Invalid or empty 'comments' list"}), 400
        
    # Use Helper
    filename = f"instagram_comments_{shortcode}.csv"
    return generate_csv_response(comments, ['Username', 'Comment'], filename)

#-----------------------------------------------------------------------------------
# --- 5. Download Analyzed CSV Routes ---
@app.route('/download_analyzed_csv', methods=['POST'])
def download_analyzed_csv_route(): 
    if not request.is_json: # Check if request is JSON
        return jsonify({"error": "Request must be JSON"}), 400

    # Get JSON data from request
    data = request.get_json()
    comments = data.get('comments') 
    filename_prefix = data.get('filename_prefix', 'analyzed_data')

    # Validate input
    if not isinstance(comments, list) or not comments:
        return jsonify({"error": "Invalid or empty 'comments' list"}), 400
        
    # Create unique filename for server storage
    saved_filename = f"{filename_prefix}_{int(time.time())}.csv"
    save_path = os.path.join(Config.DOWNLOAD_FOLDER, saved_filename)
    
    # Use Helper with save_path
    return generate_csv_response(
        comments, 
        ['Username', 'Comment', 'Sentiment'], 
        saved_filename, 
        save_path=save_path
    )

#============================================   Main   =======================================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)