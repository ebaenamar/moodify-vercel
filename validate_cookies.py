#!/usr/bin/env python3
import sys
import yt_dlp
import os
import logging
import platform
import json
import requests
import socket
from urllib.parse import urlparse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Set to True to skip actual video download test in Docker
SKIP_DOWNLOAD_TEST = os.environ.get('SKIP_DOWNLOAD_TEST', '').lower() == 'true'

# Backup proxies to try if direct connection fails
BACKUP_PROXIES = [
    'http://98.8.195.160:443',       # Fast: ~5s response
    'http://193.95.53.129:3128',     # Medium: ~24s response
    'http://45.186.6.104:3128'       # Slower: ~52s response
]

def try_with_proxies(func):
    """Try a function with different proxies if it fails."""
    def wrapper(*args, **kwargs):
        # First try without proxy
        try:
            return func(*args, **kwargs)
        except Exception as direct_error:
            logger.warning(f"Direct connection failed: {str(direct_error)}")
            
            # Try each proxy
            for proxy in BACKUP_PROXIES:
                try:
                    logger.info(f"Trying with proxy: {proxy}")
                    if 'ydl_opts' in kwargs:
                        kwargs['ydl_opts']['proxy'] = proxy
                    return func(*args, **kwargs)
                except Exception as proxy_error:
                    logger.warning(f"Proxy {proxy} failed: {str(proxy_error)}")
            
            # If all proxies fail, raise the original error
            raise direct_error
    return wrapper

def get_custom_headers():
    """Get custom headers for requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Sec-Ch-Ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
        'Sec-Ch-Ua-Mobile': '?0',
        'Sec-Ch-Ua-Platform': '"macOS"',
        'Sec-Fetch-Dest': 'document',
        'Sec-Fetch-Mode': 'navigate',
        'Sec-Fetch-Site': 'none',
        'Sec-Fetch-User': '?1',
        'Upgrade-Insecure-Requests': '1',
        'Connection': 'keep-alive',
    }

def get_ip_info():
    """Get current IP address and hosting information."""
    try:
        # Get public IP
        ip = requests.get('https://api.ipify.org').text
        # Get hostname
        hostname = socket.gethostname()
        # Get hosting provider info
        ip_info = requests.get(f'https://ipapi.co/{ip}/json/').json()
        return {
            'ip': ip,
            'hostname': hostname,
            'org': ip_info.get('org', 'Unknown'),
            'country': ip_info.get('country_name', 'Unknown'),
            'city': ip_info.get('city', 'Unknown')
        }
    except Exception as e:
        logger.warning(f"Could not get IP info: {str(e)}")
        return {'error': str(e)}

def is_running_in_docker():
    """Check if we're running inside a Docker container"""
    try:
        with open('/proc/1/cgroup', 'r') as f:
            return 'docker' in f.read()
    except:
        return False

def is_render_environment():
    """Check if we're running on Render."""
    return os.environ.get('RENDER') == 'true'

def test_youtube_connectivity():
    """Test basic connectivity to YouTube."""
    try:
        # Test DNS resolution
        youtube_ip = socket.gethostbyname('youtube.com')
        logger.info(f"YouTube DNS resolution successful: {youtube_ip}")
        
        # Test HTTPS connection
        response = requests.get('https://www.youtube.com', timeout=10)
        logger.info(f"YouTube HTTPS connection successful: {response.status_code}")
        
        return True
    except Exception as e:
        logger.error(f"YouTube connectivity test failed: {str(e)}")
        return False

@try_with_proxies
def validate_youtube_cookies():
    """
    Validate that the cookies.txt file exists and is working properly.
    Returns True if cookies are valid, False otherwise.
    """
    try:
        # Environment detection
        in_docker = is_running_in_docker()
        in_render = is_render_environment()
        logger.info(f"System info: {platform.system()} {platform.release()}")
        logger.info(f"Running in Docker: {in_docker}")
        logger.info(f"Running on Render: {in_render}")
        logger.info(f"Skip download test: {SKIP_DOWNLOAD_TEST}")
        
        # Log current working directory and cookie file location
        cwd = os.getcwd()
        cookie_path = os.path.abspath('cookies.txt')
        logger.info(f"Current working directory: {cwd}")
        logger.info(f"Looking for cookies at: {cookie_path}")
        
        # Basic file checks
        if not os.path.exists('cookies.txt'):
            logger.error("cookies.txt file not found!")
            return False
            
        # Check file permissions and size
        cookie_stats = os.stat('cookies.txt')
        logger.info(f"Cookie file size: {cookie_stats.st_size} bytes")
        logger.info(f"Cookie file permissions: {oct(cookie_stats.st_mode)[-3:]}")
        logger.info(f"Cookie file owner: {cookie_stats.st_uid}:{cookie_stats.st_gid}")
        
        if cookie_stats.st_size == 0:
            logger.error("Cookie file is empty")
            return False

        # If SKIP_DOWNLOAD_TEST is True, only check file format
        if SKIP_DOWNLOAD_TEST:
            with open('cookies.txt', 'r') as f:
                first_line = f.readline().strip()
                if '# Netscape HTTP Cookie File' in first_line:
                    logger.info("Cookie file appears to be in valid Netscape format")
                    return True
                logger.error("Cookie file is not in Netscape format")
                return False
        
        # Full validation for runtime
        # Get IP information
        ip_info = get_ip_info()
        logger.info(f"IP Information: {json.dumps(ip_info, indent=2)}")
        
        # Test YouTube connectivity
        if not test_youtube_connectivity():
            logger.error("Cannot connect to YouTube - possible IP block or network issue")
            if in_render:
                logger.error("This might be due to Render's IP being blocked by YouTube")
                logger.error("Consider using a proxy or VPN for the Render deployment")
            return False
        
        # Configure yt-dlp options with more debug info
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,  # Only extract video metadata
            'cookiefile': cookie_path,
            'verbose': True,  # Add verbose output
            'debug_printtraffic': True,  # Print all sent/received HTTP traffic
        }
        
        # Add custom headers in Docker
        if is_running_in_docker():
            headers = get_custom_headers()
            ydl_opts['http_headers'] = headers
            logger.info(f"Using custom headers: {json.dumps(headers, indent=2)}")
        
        # Validate cookie file format
        with open('cookies.txt', 'r') as f:
            cookie_content = f.read()
            logger.info(f"Cookie file first 500 chars: {cookie_content[:500]}")
            
            # Check cookie format
            if not cookie_content.startswith('# Netscape HTTP Cookie File'):
                logger.error("Cookie file does not appear to be in Netscape format")
                return False
                
            # Check for common YouTube cookies
            required_cookies = ['youtube.com', 'CONSENT', 'VISITOR_INFO1_LIVE', 'LOGIN_INFO']
            missing_cookies = [cookie for cookie in required_cookies 
                             if cookie not in cookie_content]
            
            if missing_cookies:
                logger.error(f"Missing required cookies: {missing_cookies}")
                return False
            
            logger.info("All required YouTube cookies found")
        
        logger.info(f"yt-dlp options: {json.dumps(ydl_opts, indent=2)}")
        
        # Test video - Sabrina Carpenter - Espresso
        test_url = "https://www.youtube.com/watch?v=eVli-tstM5E"
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(test_url, download=False)
                if info and 'title' in info:
                    logger.info(f"Successfully validated cookies with video: {info['title']}")
                    return True
                else:
                    logger.error("Could not extract video information")
                    return False
        except Exception as e:
            logger.error(f"yt-dlp error: {str(e)}")
            return False
        
    except Exception as e:
        logger.error(f"Cookie validation failed with error: {str(e)}")
        logger.exception("Full traceback:")
        return False

if __name__ == "__main__":
    in_docker = is_running_in_docker()
    if not validate_youtube_cookies():
        print("\n❌ ERROR: YouTube cookie validation failed!")
        if in_docker:
            print("Running in Docker environment - additional debug info:")
            print("1. Check if cookies.txt was properly copied to the container")
            print("2. Verify file permissions and ownership")
            print("3. Ensure cookies are in Netscape format")
            print("4. Check the logs above for detailed error messages")
        print("\nPlease run ./update_cookies.sh to refresh your cookies and try again.\n")
        sys.exit(1)
    
    print("\n✅ YouTube cookies validated successfully!")
    if in_docker:
        print("Cookie validation passed in Docker environment")
    print()
    sys.exit(0)
