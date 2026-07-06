from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

# ====================================================================
# Instagram Scraping Models
# ====================================================================
class InstagramScrape(db.Model):
    __tablename__ = 'instagram_scrape'
    id = db.Column(db.Integer, primary_key=True)
    shortcode = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to comments
    comments = db.relationship('InstagramComment', backref='scrape', cascade="all, delete-orphan")

class InstagramComment(db.Model):
    __tablename__ = 'instagram_comment'
    id = db.Column(db.Integer, primary_key=True)
    scrape_id = db.Column(db.Integer, db.ForeignKey('instagram_scrape.id'), nullable=False)
    username = db.Column(db.String(255))
    text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(50)) # 'positive', 'neutral', 'negative', 'N/A'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ====================================================================
# CSV Upload Models
# ====================================================================
class CsvUpload(db.Model):
    __tablename__ = 'csv_upload'
    id = db.Column(db.Integer, primary_key=True)
    filename = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship to comments
    comments = db.relationship('CsvComment', backref='upload', cascade="all, delete-orphan")

class CsvComment(db.Model):
    __tablename__ = 'csv_comment'
    id = db.Column(db.Integer, primary_key=True)
    upload_id = db.Column(db.Integer, db.ForeignKey('csv_upload.id'), nullable=False)
    username = db.Column(db.String(255))
    text = db.Column(db.Text, nullable=False)
    sentiment = db.Column(db.String(50)) # 'positive', 'neutral', 'negative', 'N/A'
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
