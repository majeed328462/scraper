import os
import logging
from flask import Flask, render_template, request, jsonify, session, redirect, url_for, flash
from scraper import MangaScraper

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "manga-scraper-secret")

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Import and initialize models
from models import db
db.init_app(app)

with app.app_context():
    # Create all tables
    db.create_all()

@app.route('/')
def index():
    """Render the main page with the manga URL input form."""
    return render_template('index.html')

@app.route('/html_tester')
def html_tester():
    """Render the HTML tester page."""
    return render_template('html_tester.html')

@app.route('/scrape', methods=['POST'])
def scrape():
    """Process the manga URL and scrape chapter links."""
    manga_url = request.form.get('manga_url', '')
    
    if not manga_url:
        return render_template('index.html', error="Please enter a manga URL")
    
    try:
        # Import here to avoid circular imports
        from models import Manga, Chapter
        
        # Check if manga already exists in database
        existing_manga = Manga.query.filter_by(url=manga_url).first()
        
        # If manga exists and has chapters, use the stored data
        if existing_manga and existing_manga.chapters:
            logger.info(f"Using stored manga data for {manga_url}")
            chapters = [
                {
                    'title': chapter.title,
                    'number': chapter.number,
                    'url': chapter.url
                } for chapter in existing_manga.chapters
            ]
            
            # Store in session for extract_images
            session['chapters'] = chapters
            session['manga_url'] = manga_url
            session['manga_id'] = existing_manga.id
            
            flash("Using stored manga data from database.", "info")
            return render_template('results.html', 
                                  manga_url=manga_url, 
                                  chapters=chapters)
        
        # Otherwise, scrape the data
        scraper = MangaScraper()
        chapters = scraper.get_chapter_links(manga_url)
        
        if not chapters:
            return render_template('index.html', 
                                  error="No chapters found for this manga. Please check the URL and try again.")
        
        # Create or update manga in database
        if not existing_manga:
            manga = Manga(url=manga_url)
            db.session.add(manga)
            db.session.commit()
        else:
            manga = existing_manga
        
        # Add new chapters to database
        for chapter_data in chapters:
            # Check if chapter already exists
            existing_chapter = Chapter.query.filter_by(
                manga_id=manga.id, 
                number=chapter_data['number']
            ).first()
            
            if not existing_chapter:
                chapter = Chapter(
                    manga_id=manga.id,
                    title=chapter_data['title'],
                    number=chapter_data['number'],
                    url=chapter_data['url']
                )
                db.session.add(chapter)
        
        # Commit all changes
        db.session.commit()
        
        # Store in session for extract_images
        session['chapters'] = chapters
        session['manga_url'] = manga_url
        session['manga_id'] = manga.id
        
        return render_template('results.html', 
                              manga_url=manga_url, 
                              chapters=chapters)
    
    except Exception as e:
        logger.error(f"Error scraping manga: {str(e)}", exc_info=True)
        return render_template('index.html', 
                              error=f"Error scraping manga: {str(e)}")

@app.route('/extract_images', methods=['POST'])
def extract_images():
    """Extract images from selected chapters."""
    selected_chapters = request.form.getlist('selected_chapters')
    manga_url = session.get('manga_url', '')
    manga_id = session.get('manga_id')
    chapters = session.get('chapters', [])
    
    if not selected_chapters or not manga_url or not chapters:
        return redirect(url_for('index'))
    
    try:
        # Import here to avoid circular imports
        from models import Chapter, Image
        
        scraper = MangaScraper()
        results = {}
        
        for chapter_num in selected_chapters:
            chapter_info = next((ch for ch in chapters if ch['number'] == chapter_num), None)
            if not chapter_info:
                continue
                
            # Find chapter in database
            db_chapter = Chapter.query.filter_by(
                manga_id=manga_id, 
                number=chapter_num
            ).first()
            
            # If chapter not found in database, create it
            if not db_chapter and manga_id:
                db_chapter = Chapter(
                    manga_id=manga_id,
                    title=chapter_info['title'],
                    number=chapter_num,
                    url=chapter_info['url']
                )
                db.session.add(db_chapter)
                db.session.commit()
            
            # Check if chapter already has images in database
            if db_chapter and db_chapter.images:
                logger.info(f"Using stored images for chapter {chapter_num}")
                image_urls = [img.url for img in db_chapter.images]
            else:
                # Scrape images
                image_urls = scraper.extract_image_urls(chapter_info['url'])
                
                # Store images in database if we have a valid chapter
                if db_chapter and image_urls:
                    for idx, url in enumerate(image_urls):
                        # Check if image already exists
                        existing_image = Image.query.filter_by(
                            chapter_id=db_chapter.id,
                            url=url
                        ).first()
                        
                        if not existing_image:
                            image = Image(
                                chapter_id=db_chapter.id,
                                url=url,
                                sequence=idx + 1
                            )
                            db.session.add(image)
                    
                    db.session.commit()
            
            results[chapter_num] = {
                'title': chapter_info['title'],
                'url': chapter_info['url'],
                'images': image_urls
            }
        
        return render_template('results.html', 
                              manga_url=manga_url, 
                              chapters=chapters,
                              results=results)
    
    except Exception as e:
        logger.error(f"Error extracting images: {str(e)}", exc_info=True)
        return render_template('results.html', 
                              manga_url=manga_url, 
                              chapters=chapters,
                              error=f"Error extracting images: {str(e)}")

@app.route('/api/extract_single_chapter', methods=['POST'])
def extract_single_chapter():
    """API endpoint to extract images from a single chapter."""
    data = request.json
    chapter_url = data.get('chapter_url')
    
    if not chapter_url:
        return jsonify({'error': 'Chapter URL is required'}), 400
    
    try:
        # Import here to avoid circular imports
        from models import Chapter, Image
        
        # Check if we already have this chapter in database
        db_chapter = Chapter.query.filter_by(url=chapter_url).first()
        
        # If chapter exists and has images, use the stored data
        if db_chapter and db_chapter.images:
            logger.info(f"Using stored images for chapter URL: {chapter_url}")
            image_urls = [img.url for img in db_chapter.images]
        else:
            # Otherwise, scrape the images
            scraper = MangaScraper()
            image_urls = scraper.extract_image_urls(chapter_url)
            
            # Store images if we have a valid chapter
            if db_chapter and image_urls:
                for idx, url in enumerate(image_urls):
                    # Check if image already exists
                    existing_image = Image.query.filter_by(
                        chapter_id=db_chapter.id,
                        url=url
                    ).first()
                    
                    if not existing_image:
                        image = Image(
                            chapter_id=db_chapter.id,
                            url=url,
                            sequence=idx + 1
                        )
                        db.session.add(image)
                
                db.session.commit()
                
        return jsonify({
            'success': True,
            'image_urls': image_urls
        })
    except Exception as e:
        logger.error(f"Error extracting images from chapter: {str(e)}", exc_info=True)
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
