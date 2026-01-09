from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import pandas as pd

# Initialize VADER analyzer globally to avoid overhead on every call
analyzer = SentimentIntensityAnalyzer()

#==================================== CUSTOM LEXICON UPDATE =================================
# To fix and customize inverted scores for common slang/emojis
modern_slang = {
    # --- POSITIVE ---
    'fire': 3.5,      
    'lit': 3.0,
    'based': 3.0,
    'goated': 3.5,
    'w': 2.0,          
    'banger': 3.0,
    'peak': 3.0,
    'heart': 2.5,
    
    # --- NEUTRAL ---       

    # --- NEGATIVE ---
    'robbery': -3.0,  
    'scam': -3.5,
    'trash': -3.0,
    'mid': -2.0,
    'l': -2.0,        
    'cringe': -2.5,
    'clown': -2.0,     
    'fraud': -3.0,
    'rip': -1.5,    
}

analyzer.lexicon.update(modern_slang)

#==================================== Sentiment Analysis Functions ================================
# 1. Function to analyze sentiment of a single string
def analyze_sentiment_text(text):
    # Convert to string if necessary
    if isinstance(text, (float, int)):
        text = str(text)
    
    # Score the text
    scores = analyzer.polarity_scores(text)
    compound = scores['compound']
    
    # Return sentiment based on compound score
    if compound >= 0.05:
        return 'Positive'
    elif compound <= -0.05:
        return 'Negative'
    else:
        return 'Neutral'

#-----------------------------------------------------------------------------------
# 2. Function to process CSV file and add sentiment analysis
def process_csv_sentiment(filepath):
    # Try evaluating with utf-8-sig to handle BOM if present, and replace errors to avoid crash
    try:
        try:
             df = pd.read_csv(filepath, encoding='utf-8')

        # Fallback if utf-8 fails (e.g. excel generated csvs)     
        except UnicodeDecodeError:
             df = pd.read_csv(filepath, encoding='cp1252', encoding_errors='replace')
        
        # Normalize column names
        if 'Comment' in df.columns:
            df.rename(columns={'Comment': 'comment'}, inplace=True)
        if 'Username' in df.columns:
            df.rename(columns={'Username': 'username'}, inplace=True)    
        if 'comment' not in df.columns:
            return None, None, "CSV must have a 'comment' or 'Comment' column."

        # Filter empty rows BEFORE analysis to avoid Neutral tags on blanks
        df.dropna(subset=['comment'], inplace=True)
        df['comment'] = df['comment'].astype(str)
        df = df[df['comment'].str.strip() != '']

        # Analyze
        df['sentiment'] = df['comment'].apply(analyze_sentiment_text)
        
        # Fill NaNs in OTHER columns (like username if missing) to avoid JSON errors
        df = df.fillna('')

        # Get Sentiment Counts
        sentiment_counts = df['sentiment'].value_counts().to_dict()

        # Get Comments Data
        comments_data = df.to_dict(orient='records')
        
        # Return ALL columns (including username) instead of just subset
        return sentiment_counts, comments_data, None
        
    # Exception Handling for any other errors     
    except Exception as e:
        return None, None, f"Processing Error: {str(e)}"
