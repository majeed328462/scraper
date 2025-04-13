import re
import logging
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

class MangaScraper:
    """Class for scraping manga websites to extract chapter links and image URLs."""
    
    def __init__(self):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
    
    def get_chapter_links(self, manga_url):
        """
        Extract chapter links from the provided manga URL.
        
        Args:
            manga_url (str): URL of the manga main page
            
        Returns:
            list: List of dictionaries containing chapter info (title, number, url)
        """
        logger.debug(f"Fetching chapter links from URL: {manga_url}")
        
        try:
            response = requests.get(manga_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find the table containing chapters
            # The table structure is based on the HTML snippet provided
            chapter_table = soup.select_one("div.max-h-\\[40vh\\] table")
            
            if not chapter_table:
                logger.warning("Chapter table not found on the page")
                # Try alternative selectors
                chapter_table = soup.select_one("table")
            
            if not chapter_table:
                logger.error("Could not find any chapter table on the page")
                return []
            
            chapters = []
            
            # Process rows in the table
            for row in chapter_table.select("tbody tr"):
                try:
                    # Extract chapter name/title
                    title_cell = row.select_one("td:first-child")
                    if not title_cell:
                        continue
                        
                    title = title_cell.get_text(strip=True)
                    
                    # Extract chapter number using regex
                    chapter_num_match = re.search(r'Chapter\s+([0-9.]+)', title)
                    if chapter_num_match:
                        chapter_num = chapter_num_match.group(1)
                    else:
                        # Try to find any number in the title
                        number_match = re.search(r'([0-9.]+)', title)
                        chapter_num = number_match.group(1) if number_match else "unknown"
                    
                    # Find link to chapter
                    link = row.select_one("a[href]")
                    if not link:
                        continue
                        
                    chapter_url = link.get('href')
                    
                    # Make sure URL is absolute
                    if not chapter_url.startswith(('http://', 'https://')):
                        chapter_url = urljoin(manga_url, chapter_url)
                    
                    chapters.append({
                        'title': title,
                        'number': chapter_num,
                        'url': chapter_url
                    })
                    
                except Exception as e:
                    logger.error(f"Error processing chapter row: {str(e)}")
                    continue
            
            # Sort chapters by number (convert to float for proper numeric sorting)
            def chapter_sort_key(chapter):
                try:
                    return float(chapter['number'])
                except (ValueError, TypeError):
                    return 0
                    
            chapters.sort(key=chapter_sort_key)
            
            logger.info(f"Found {len(chapters)} chapters")
            return chapters
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to fetch the manga page: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing manga page: {str(e)}")
            raise Exception(f"Failed to parse the manga page: {str(e)}")
    
    def extract_image_urls(self, chapter_url):
        """
        Extract image URLs from a specific chapter page.
        
        Args:
            chapter_url (str): URL of the chapter page
            
        Returns:
            list: List of image URLs for the chapter
        """
        logger.debug(f"Extracting images from chapter URL: {chapter_url}")
        
        try:
            response = requests.get(chapter_url, headers=self.headers)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Look for common manga image containers
            image_containers = soup.select(".chapter-content img, .reader-area img, .manga-images img, .manga-container img")
            
            # If none found, try more generic selectors
            if not image_containers:
                # Look for any large images that are likely manga panels
                image_containers = soup.select("img[src*=chapter], img[src*=manga], img[src*=content], img[data-src]")
            
            if not image_containers:
                # Last resort: look for any images with specific attributes or patterns
                image_containers = soup.select("img[width], img[height]")
            
            image_urls = []
            
            # Process each image container
            for img in image_containers:
                # Check for lazy loading
                src = img.get('data-src') or img.get('data-lazy-src') or img.get('src')
                
                if src:
                    # Make sure URL is absolute
                    if not src.startswith(('http://', 'https://')):
                        src = urljoin(chapter_url, src)
                    
                    # Avoid duplicates
                    if src not in image_urls:
                        image_urls.append(src)
            
            # If no images found, try to find them in JavaScript
            if not image_urls:
                # Look for image URLs in JavaScript variables
                scripts = soup.select("script")
                for script in scripts:
                    script_text = script.string
                    if script_text:
                        # Look for arrays of image URLs
                        image_matches = re.findall(r'["\'](https?://[^"\']+\.(jpg|jpeg|png|webp))["\']', script_text)
                        for match in image_matches:
                            if match[0] not in image_urls:
                                image_urls.append(match[0])
            
            logger.info(f"Found {len(image_urls)} images in chapter")
            return image_urls
            
        except requests.RequestException as e:
            logger.error(f"Request error: {str(e)}")
            raise Exception(f"Failed to fetch the chapter page: {str(e)}")
        except Exception as e:
            logger.error(f"Error parsing chapter page: {str(e)}")
            raise Exception(f"Failed to parse the chapter page: {str(e)}")
