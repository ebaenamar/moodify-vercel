#!/usr/bin/env python3
import sys
import yt_dlp
import os
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def get_custom_headers():
    """Get custom headers for requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate',
        'Connection': 'keep-alive',
    }

def validate_youtube_cookies():
    """
    Validate that the cookies.txt file exists and is working properly.
    Returns True if cookies are valid, False otherwise.
    """
    try:
        logger.info("Validating YouTube cookies...")
        
        # Log current working directory and cookie file location
        cwd = os.getcwd()
        cookie_path = os.path.abspath('cookies.txt')
        logger.info(f"Current working directory: {cwd}")
        logger.info(f"Looking for cookies at: {cookie_path}")
        
        if not os.path.exists('cookies.txt'):
            logger.error("cookies.txt file not found!")
            return False
            
        # Log cookie file size and last modified time
        cookie_stats = os.stat('cookies.txt')
        logger.info(f"Cookie file size: {cookie_stats.st_size} bytes")
        logger.info(f"Cookie file last modified: {os.path.getmtime(cookie_path)}")
        
        # Log first few lines of cookie file (without sensitive data)
        with open('cookies.txt', 'r') as f:
            first_lines = [next(f) for _ in range(3)]
            logger.info("Cookie file header:")
            for line in first_lines:
                if line.startswith('#'):  # Only log comment lines
                    logger.info(f"  {line.strip()}")
            
        # Test video - Sabrina Carpenter - Espresso
        test_url = "https://www.youtube.com/watch?v=eVli-tstM5E"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'no_check_certificate': True,
            'cookiefile': cookie_path,
            'http_headers': get_custom_headers()
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Attempting to extract video info with cookies...")
            info = ydl.extract_info(test_url, download=False)
            if info and 'title' in info:
                logger.info(f"Cookie validation successful! Video title: {info['title']}")
                return True
            else:
                logger.error("Cookie validation failed: couldn't extract video info")
                return False
    except Exception as e:
        logger.error(f"Cookie validation failed with error: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    if not validate_youtube_cookies():
        print("\n❌ ERROR: YouTube cookie validation failed!")
        print("The cookies.txt file exists but is not working in the Docker environment.")
        print("Please run ./update_cookies.sh to refresh your cookies and try again.\n")
        sys.exit(1)
    else:
        print("\n✅ YouTube cookies validated successfully in Docker!\n")
