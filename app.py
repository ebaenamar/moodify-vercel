from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import yt_dlp
import os
import tempfile
import uuid
import subprocess
import logging
import traceback
import re
from werkzeug.utils import secure_filename
import requests
import moviepy.editor as mp
import time

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://moodi-fy.vercel.app",
            "http://localhost:3000",
            "http://localhost:5000",
            "http://127.0.0.1:5000"
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Device-Info"],
        "expose_headers": ["Content-Disposition"],
        "supports_credentials": True
    }
})

def validate_youtube_cookies():
    """
    Validate that the cookies.txt file exists and is working properly.
    Returns True if cookies are valid, False otherwise.
    """
    try:
        logger.info("Validating YouTube cookies...")
        if not os.path.exists('cookies.txt'):
            logger.error("cookies.txt file not found!")
            return False
            
        # Test video ID (a popular video that's unlikely to be taken down)
        test_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
        
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'cookiefile': os.path.abspath('cookies.txt')
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(test_url, download=False)
            if info and 'title' in info:
                logger.info("YouTube cookies validated successfully!")
                return True
            else:
                logger.error("Cookie validation failed: couldn't extract video info")
                return False
    except Exception as e:
        logger.error(f"Cookie validation failed with error: {str(e)}")
        return False

@app.after_request
def after_request(response):
    origin = request.headers.get('Origin')
    if origin and (origin.endswith('.vercel.app') or origin.startswith('http://localhost')):
        response.headers.add('Access-Control-Allow-Origin', origin)
    else:
        response.headers.add('Access-Control-Allow-Origin', 'https://moodi-fy.vercel.app')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
    response.headers.add('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
    return response

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temporary directories for processing
TEMP_DIR = os.environ.get('TEMP_DIR', tempfile.mkdtemp())
OUTPUT_DIR = os.path.join(TEMP_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

logger.info(f"Temporary directory created at: {TEMP_DIR}")
logger.info(f"Output directory created at: {OUTPUT_DIR}")

def get_custom_headers():
    """Get custom headers for YouTube requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def extract_video_id(url):
    """Extract video ID from various YouTube URL formats."""
    if match := re.search(r'(?:v=|/v/|youtu\.be/)([^"&?/\s]{11})', url):
        return match.group(1)
    raise ValueError("Could not extract video ID from URL")

def get_fresh_cookies_docker(url):
    """Get fresh cookies using yt-dlp's --cookies-from-browser in Docker."""
    logger.info("Attempting to get fresh cookies in Docker environment")
    cookies_path = os.path.join(TEMP_DIR, 'fresh_cookies.txt')
    
    try:
        # Configure yt-dlp options for cookie extraction
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'cookiesfrombrowser': ('chrome', None),  # Use Chrome without specific profile
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Extracting cookies from Chrome")
            ydl.extract_info(url, download=False)
            
            # The cookies should now be in yt-dlp's cookie jar
            # We need to save them to a file
            if hasattr(ydl, '_get_cookies'):
                cookies = ydl._get_cookies(url)
                with open(cookies_path, 'w') as f:
                    for cookie in cookies:
                        f.write(f'{cookie.domain}\tTRUE\t{cookie.path}\t'
                               f'{"TRUE" if cookie.secure else "FALSE"}\t{cookie.expires}\t'
                               f'{cookie.name}\t{cookie.value}\n')
                logger.info(f"Successfully saved fresh cookies to {cookies_path}")
                return cookies_path
    except Exception as e:
        logger.error(f"Error getting fresh cookies in Docker: {str(e)}")
    
    return None

def download_audio(url, output_path, cookies_path=None):
    """Download audio from a YouTube video."""
    try:
        # Validate cookies before attempting download
        if not validate_youtube_cookies():
            logger.error("Cookie validation failed before download attempt")
            raise Exception("YouTube cookies are invalid or expired. Please refresh cookies and redeploy.")

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': output_path,
            'quiet': True,
            'no_warnings': True
        }

        if cookies_path and os.path.exists('cookies.txt'):
            logger.info("Using existing cookies.txt file")
            cookies_path = os.path.abspath('cookies.txt')
            ydl_opts['cookiefile'] = cookies_path

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading audio from: {url}")
            ydl.download([url])
            
        if not os.path.exists(output_path):
            raise Exception(f"Download completed but file not found at {output_path}")
            
        return True

    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        raise

def apply_audio_effect(input_path, output_path, effect_type='slow_reverb'):
    """Apply audio effect using FFmpeg."""
    try:
        logger.info(f"Input path exists: {os.path.exists(input_path)}")
        logger.info(f"Input path size: {os.path.getsize(input_path) if os.path.exists(input_path) else 'file not found'}")
        
        # Define effect parameters for each vibe
        effect_params = {
            'slow_reverb': {
                'speed': 0.85,
                'reverb_delay': 60,
                'reverb_decay': 0.4
            },
            'energetic': {
                'speed': 1.2,
                'reverb_delay': 20,
                'reverb_decay': 0.2
            },
            'dark': {
                'speed': 0.8,
                'reverb_delay': 100,
                'reverb_decay': 0.6
            },
            'cute': {
                'speed': 1.1,
                'reverb_delay': 30,
                'reverb_decay': 0.3
            },
            'cool': {
                'speed': 0.95,
                'reverb_delay': 50,
                'reverb_decay': 0.5
            },
            'happy': {
                'speed': 1.05,
                'reverb_delay': 40,
                'reverb_decay': 0.3
            },
            'intense': {
                'speed': 1.15,
                'reverb_delay': 25,
                'reverb_decay': 0.2
            },
            'melodic': {
                'speed': 1.0,
                'reverb_delay': 70,
                'reverb_decay': 0.5
            },
            'chill': {
                'speed': 0.9,
                'reverb_delay': 80,
                'reverb_decay': 0.4
            },
            'sleepy': {
                'speed': 0.75,
                'reverb_delay': 90,
                'reverb_decay': 0.7
            }
        }
        
        # Get effect parameters or use default
        params = effect_params.get(effect_type, effect_params['slow_reverb'])
        
        # Build FFmpeg command with parameters
        filter_complex = (
            f'[0:a]asetrate=44100*{params["speed"]},aresample=44100,atempo=1.0[s];'
            f'[s]aecho=0.8:0.88:{params["reverb_delay"]}:{params["reverb_decay"]}[e]'
        )
        
        cmd = [
            'ffmpeg', '-y', '-i', input_path,
            '-filter_complex', filter_complex,
            '-map', '[e]',
            '-acodec', 'libmp3lame', '-q:a', '2',
            output_path
        ]

        logger.info(f"Running FFmpeg command: {' '.join(cmd)}")
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        logger.info(f"FFmpeg stdout: {result.stdout}")
        logger.info(f"FFmpeg stderr: {result.stderr}")
        
        if not os.path.exists(output_path):
            logger.error("Output file was not created")
            return False
            
        logger.info(f"Output file created successfully, size: {os.path.getsize(output_path)}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error in apply_audio_effect: {str(e)}")
        logger.error(traceback.format_exc())
        return False

def sanitize_filename(filename):
    """Sanitize filename by removing invalid characters."""
    # Remove invalid filename characters
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    # Limit length
    return filename[:100]

def process_youtube_audio(url, effect_type='slow_reverb'):
    """Download and process YouTube audio."""
    download_path = None
    try:
        logger.info(f"Processing YouTube URL: {url}")
        
        # Extract video ID and construct clean URL
        video_id = extract_video_id(url)
        if not video_id:
            raise ValueError("Invalid YouTube URL format")
            
        clean_url = f"https://www.youtube.com/watch?v={video_id}"
        logger.info(f"Clean YouTube URL: {clean_url}")
        
        # Get video info to extract title
        with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
            info = ydl.extract_info(url, download=False)
            video_title = info.get('title', video_id)
        
        # Generate filename using title and effect
        safe_title = sanitize_filename(video_title)
        temp_filename = f"{safe_title}"
        final_filename = f"{safe_title}_{effect_type}"
        
        download_path = os.path.join(TEMP_DIR, temp_filename)
        output_path = os.path.join(OUTPUT_DIR, f"{final_filename}.mp3")

        # Download the audio
        downloaded_file = download_audio(clean_url, download_path)
        logger.info(f"Download completed, file size: {os.path.getsize(downloaded_file)}")

        # Convert and apply effect
        logger.info("Applying audio effect...")
        if not apply_audio_effect(downloaded_file, output_path, effect_type):
            raise ValueError("Failed to process audio with effects")
        logger.info("Audio effect applied successfully")

        # Clean up downloaded file
        os.remove(downloaded_file)
        logger.info("Cleaned up temporary files")

        return output_path, final_filename

    except ValueError as e:
        # Re-raise user-friendly errors
        raise
    except Exception as e:
        logger.error(f"Error in process_youtube_audio: {str(e)}")
        logger.error(traceback.format_exc())
        if download_path and os.path.exists(download_path + '.mp3'):
            os.remove(download_path + '.mp3')
        raise ValueError("An unexpected error occurred while processing the video")

@app.route('/')
def root():
    """Root endpoint to verify the server is running"""
    return jsonify({
        'status': 'ok',
        'message': 'Moodify API is running',
        'endpoints': [
            '/api/test',
            '/api/health',
            '/api/transform (POST)'
        ]
    })

@app.route('/api/test', methods=['GET', 'OPTIONS'])
def test_cors():
    """Test endpoint for CORS"""
    return jsonify({'status': 'ok'})

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'temp_dir': TEMP_DIR,
        'output_dir': OUTPUT_DIR
    }), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

@app.route('/api/download', methods=['POST'])
def download():
    try:
        data = request.get_json()
        if not data or 'url' not in data:
            return jsonify({'error': 'No URL provided'}), 400

        url = data['url']
        effect_type = data.get('effect_type', 'slow_reverb')
        cookies = data.get('cookies')  # Get cookies from request if available

        # Validate YouTube URL
        if not extract_video_id(url):
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Try different cookie methods
        cookies_path = None
        
        # 1. Try cookies from request
        if cookies:
            logger.info("Received cookies from browser, writing to cookies.txt")
            cookies_path = os.path.join(TEMP_DIR, 'cookies.txt')
            with open(cookies_path, 'w') as f:
                f.write("# Netscape HTTP Cookie File\n")
                f.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
                f.write("# This is a generated file!  Do not edit.\n\n")
                
                # Parse cookies string from browser
                for cookie in cookies.split(';'):
                    if '=' in cookie:
                        name, value = cookie.strip().split('=', 1)
                        # Set a default expiration of 1 year from now
                        expires = str(int(time.time()) + 31536000)
                        f.write(f".youtube.com\tTRUE\t/\tTRUE\t{expires}\t{name}\t{value}\n")
            logger.info(f"Successfully wrote browser cookies to file")
        
        # 2. If no cookies in request or writing failed, try using cookies.txt
        if not cookies_path and os.path.exists('cookies.txt'):
            logger.info("Using existing cookies.txt file")
            cookies_path = os.path.abspath('cookies.txt')
        
        # 3. If still no cookies, try getting them from Chrome
        if not cookies_path:
            logger.info("Getting fresh cookies from Chrome")
            try:
                subprocess.run([
                    'yt-dlp',
                    '--cookies-from-browser', 'chrome',
                    '--cookies', 'temp_cookies.txt',
                    '--quiet',
                    url
                ], check=True)
                if os.path.exists('temp_cookies.txt'):
                    cookies_path = os.path.abspath('temp_cookies.txt')
                    logger.info("Successfully got cookies from Chrome")
            except Exception as e:
                logger.error(f"Error getting Chrome cookies: {str(e)}")

        # Process the audio
        try:
            output_path, filename = process_youtube_audio(url, effect_type)
            
            # Clean up temporary cookies file
            if cookies_path and os.path.basename(cookies_path) == 'temp_cookies.txt':
                try:
                    os.remove(cookies_path)
                except:
                    pass
                    
        except Exception as e:
            logger.error(f"Error downloading audio: {str(e)}")
            return jsonify({'error': str(e)}), 500

        # Return the file
        return send_file(output_path, as_attachment=True, download_name=f"{filename}.mp3")
    except Exception as e:
        logger.error(f"Error in download endpoint: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': str(e)}), 500

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    try:
        data = request.get_json()
        logger.info(f"Received request data: {data}")
        
        if not data or 'url' not in data:
            logger.error("No URL provided in request")
            return jsonify({'error': 'No URL provided'}), 400
        
        url = data['url']
        effect_type = data.get('effect_type', 'slow_reverb')
        
        logger.info(f"Processing URL: {url} with effect: {effect_type}")
        
        # Process the audio
        output_path, filename = process_youtube_audio(url, effect_type)
        
        if not os.path.exists(output_path):
            logger.error("Output file not found after processing")
            return jsonify({'error': 'Failed to create output file'}), 500
        
        logger.info(f"Sending processed file: {output_path}")
        # Return the processed file
        return send_file(
            output_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"{filename}.mp3"
        )

    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    # Validate cookies on startup
    if not validate_youtube_cookies():
        logger.error("⚠️ WARNING: YouTube cookies validation failed! The application may not work correctly.")
        logger.error("Please run ./update_cookies.sh to refresh your cookies and redeploy.")
    
    port = int(os.environ.get('PORT', 5005))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
