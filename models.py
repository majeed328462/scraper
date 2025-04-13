from datetime import datetime
from flask_sqlalchemy import SQLAlchemy

# This will be initialized in app.py
db = SQLAlchemy()

class Manga(db.Model):
    """Model for manga information."""
    id = db.Column(db.Integer, primary_key=True)
    url = db.Column(db.String(255), unique=True, nullable=False)
    title = db.Column(db.String(255))
    description = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationship with chapters
    chapters = db.relationship('Chapter', backref='manga', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Manga {self.title}>'

class Chapter(db.Model):
    """Model for manga chapters."""
    id = db.Column(db.Integer, primary_key=True)
    manga_id = db.Column(db.Integer, db.ForeignKey('manga.id'), nullable=False)
    number = db.Column(db.String(20), nullable=False)
    title = db.Column(db.String(255))
    url = db.Column(db.String(255), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship with images
    images = db.relationship('Image', backref='chapter', lazy=True, cascade="all, delete-orphan")
    
    def __repr__(self):
        return f'<Chapter {self.number} - {self.title}>'

class Image(db.Model):
    """Model for manga chapter images."""
    id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapter.id'), nullable=False)
    url = db.Column(db.Text, nullable=False)
    sequence = db.Column(db.Integer)  # Order of image in chapter
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Image {self.sequence} for Chapter {self.chapter_id}>'