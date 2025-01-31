from flask import Flask, request, jsonify, send_file, Response
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
import datetime
import glob
import shutil

app = Flask(__name__)

# Configure CORS
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://moodi-fy.vercel.app",
            "http://localhost:3000",
            "http://localhost:5000",
            "http://127.0.0.1:5000",
            "https://*.vercel.app",
            "capacitor://*",  # For mobile apps
            "ionic://*"       # For mobile apps
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type", "Authorization", "X-Device-Info", "Range", "Accept", "Origin"],
        "expose_headers": ["Content-Disposition", "Content-Range", "Content-Length", "Accept-Ranges"],
        "supports_credentials": True,
        "max_age": 600
    }
})

def get_client_ip():
    """Get the real client IP accounting for proxies."""
    if 'Cf-Connecting-Ip' in request.headers:
        return request.headers['Cf-Connecting-Ip']
    if 'X-Forwarded-For' in request.headers:
        return request.headers['X-Forwarded-For'].split(',')[0].strip()
    return request.remote_addr

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    """Add CORS headers to all responses."""
    origin = request.headers.get('Origin')
    
    # Log the origin and request details
    app.logger.info(f"Request Origin: {origin}")
    app.logger.info(f"Client IP: {get_client_ip()}")
    
    # Only allow specific origins
    if origin:
        if origin.startswith(('https://moodi-fy.vercel.app', 'http://localhost', 'capacitor://', 'ionic://')):
            response.headers['Access-Control-Allow-Origin'] = origin
    
    response.headers['Access-Control-Allow-Methods'] = 'GET, POST, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-Device-Info, Range, Accept, Origin'
    response.headers['Access-Control-Expose-Headers'] = 'Content-Disposition, Content-Range, Content-Length, Accept-Ranges'
    response.headers['Access-Control-Max-Age'] = '600'
    
    # Add security headers
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return response
        
    return response

@app.before_request
def log_request_info():
    """Log details about every request."""
    app.logger.info('=' * 50)
    app.logger.info(f'Request Method: {request.method}')
    app.logger.info(f'Request URL: {request.url}')
    app.logger.info(f'Request Headers: {dict(request.headers)}')
    app.logger.info(f'Request Args: {dict(request.args)}')
    if request.is_json:
        app.logger.info(f'Request JSON: {request.get_json()}')
    app.logger.info('=' * 50)

@app.after_request
def log_response_info(response):
    """Log details about every response."""
    app.logger.info('-' * 50)
    app.logger.info(f'Response Status: {response.status}')
    app.logger.info(f'Response Headers: {dict(response.headers)}')
    app.logger.info('-' * 50)
    return response

@app.errorhandler(Exception)
def handle_exception(e):
    """Log any exceptions that occur."""
    app.logger.error('!' * 50)
    app.logger.error(f'Exception occurred: {str(e)}')
    app.logger.error(traceback.format_exc())
    app.logger.error('!' * 50)
    return jsonify({'error': str(e)}), 500

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
        logger.info(f"Cookie file last modified: {datetime.datetime.fromtimestamp(cookie_stats.st_mtime)}")
        
        # Log first few lines of cookie file (without sensitive data)
        with open('cookies.txt', 'r') as f:
            first_lines = [next(f) for _ in range(3)]
            logger.info("Cookie file header:")
            for line in first_lines:
                if line.startswith('#'):  # Only log comment lines
                    logger.info(f"  {line.strip()}")
            
        # Test video - Sabrina Carpenter - Espresso
        test_url = "https://www.youtube.com/watch?v=eVli-tstM5E"
        
        ydl_opts = get_ydl_opts('cookies.txt')
        ydl_opts['extract_flat'] = True  # Only fetch metadata
        
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

def get_custom_headers():
    """Get custom headers for YouTube requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
    }

def get_ydl_opts(cookies_path=None):
    """Get consistent yt-dlp options across all functions."""
    opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        'extract_flat': True,
        'no_check_certificate': True,
        'http_headers': get_custom_headers(),
        'socket_timeout': 30,
        'retries': 3
    }
    
    if cookies_path and os.path.exists(cookies_path):
        cookie_path = os.path.abspath(cookies_path)
        logger.info(f"Using cookies from: {cookie_path}")
        
        # Log cookie file details
        try:
            cookie_stats = os.stat(cookie_path)
            logger.info(f"Cookie file size: {cookie_stats.st_size} bytes")
            logger.info(f"Cookie permissions: {oct(cookie_stats.st_mode)[-3:]}")
            logger.info(f"Cookie last modified: {datetime.datetime.fromtimestamp(cookie_stats.st_mtime)}")
            
            # Check if file is readable
            if not os.access(cookie_path, os.R_OK):
                logger.error(f"Cookie file is not readable! Permissions: {oct(cookie_stats.st_mode)[-3:]}")
                return opts
            
            # Verify cookie file format
            with open(cookie_path, 'r') as f:
                first_line = f.readline().strip()
                if not first_line.startswith('# Netscape HTTP Cookie File'):
                    logger.error("Cookie file appears to be invalid - wrong header")
                    return opts
                
            opts['cookiefile'] = cookie_path
        except Exception as e:
            logger.error(f"Error checking cookie file: {str(e)}")
    
    return opts

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
        logger.info(f"Starting download for URL: {url}")
        logger.info(f"Output path: {output_path}")
        
        # Get options with cookie validation
        ydl_opts = get_ydl_opts('cookies.txt')
        ydl_opts['extract_flat'] = False
        ydl_opts['outtmpl'] = output_path
        
        # Log all options (excluding sensitive data)
        safe_opts = {k:v for k,v in ydl_opts.items() if k not in ['cookiefile']}
        logger.info(f"Download options: {safe_opts}")
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info(f"Downloading audio from: {url}")
            ydl.download([url])
            
        if not os.path.exists(output_path):
            raise Exception(f"Download completed but file not found at {output_path}")
            
        # Log success details
        file_size = os.path.getsize(output_path)
        logger.info(f"Download successful! File size: {file_size} bytes")
        return True

    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        logger.exception("Full traceback:")
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

def is_mobile_request():
    """Check if the request is coming from a mobile device."""
    user_agent = request.headers.get('User-Agent', '').lower()
    mobile_keywords = ['mobile', 'android', 'iphone', 'ipad', 'ipod']
    return any(keyword in user_agent for keyword in mobile_keywords)

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

@app.route('/api/download', methods=['POST', 'OPTIONS'])
def process_youtube():
    """Process a YouTube video URL."""
    # Handle preflight requests
    if request.method == 'OPTIONS':
        return '', 204
        
    try:
        is_mobile = is_mobile_request()
        client_ip = get_client_ip()
        app.logger.info(f"Processing request from {'mobile' if is_mobile else 'desktop'} device. Client IP: {client_ip}")
        
        if not request.is_json:
            app.logger.error("Request must be JSON")
            return jsonify({'error': 'Request must be JSON'}), 400
        
        request_data = request.get_json()
        app.logger.info(f"Request data: {request_data}")

        if not request_data or 'url' not in request_data:
            app.logger.error("Invalid request: missing URL")
            return jsonify({'error': 'Missing URL parameter'}), 400

        url = request_data['url']
        app.logger.info(f"Processing URL: {url}")

        # Verify cookies file exists and is readable
        cookie_file = 'cookies.txt'
        if not os.path.exists(cookie_file):
            app.logger.error("Cookie file not found")
            return jsonify({'error': 'Cookie file not found'}), 500
        
        app.logger.info(f"Cookie file stats: size={os.path.getsize(cookie_file)}, last_modified={os.path.getmtime(cookie_file)}")
        
        try:
            with open(cookie_file, 'r') as f:
                cookie_content = f.read()
                app.logger.info(f"Cookie file is readable, length: {len(cookie_content)}")
        except Exception as e:
            app.logger.error(f"Error reading cookie file: {str(e)}")
            return jsonify({'error': 'Could not read cookie file'}), 500

        # Create temp directory if it doesn't exist
        temp_dir = os.environ.get('TEMP_DIR', '/app/temp')
        output_dir = os.environ.get('OUTPUT_DIR', '/app/output')
        
        os.makedirs(temp_dir, exist_ok=True)
        os.makedirs(output_dir, exist_ok=True)
        
        app.logger.info(f"Using directories - temp: {temp_dir}, output: {output_dir}")
        app.logger.info(f"Directory permissions - temp: {oct(os.stat(temp_dir).st_mode)}, output: {oct(os.stat(output_dir).st_mode)}")

        # Download audio using yt-dlp
        ydl_opts = {
            'format': 'bestaudio/best',
            'cookiesfrombrowser': None,  # Disable browser cookies
            'cookiefile': cookie_file,
            'extract_audio': True,
            'outtmpl': f'{temp_dir}/%(title)s.%(ext)s',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'verbose': True,  # Enable verbose output for debugging
            'quiet': False,
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                app.logger.info("Starting video info extraction")
                video_info = ydl.extract_info(url, download=False)
                app.logger.info(f"Video info extracted successfully: {video_info.get('title', 'No title')}")
                
                app.logger.info("Starting video download")
                ydl.download([url])
                app.logger.info("Video download completed")
        except Exception as e:
            app.logger.error(f"Error in yt-dlp operation: {str(e)}")
            return jsonify({'error': f'YouTube download failed: {str(e)}'}), 500

        # Find the downloaded file
        downloaded_files = glob.glob(f"{temp_dir}/*.mp3")
        if not downloaded_files:
            app.logger.error("No MP3 file found after download")
            return jsonify({'error': 'No audio file found after download'}), 500

        input_file = downloaded_files[0]
        app.logger.info(f"Found downloaded file: {input_file}")

        # Generate output filename
        output_filename = f"{os.path.splitext(os.path.basename(input_file))[0]}_processed.mp3"
        output_file = os.path.join(output_dir, output_filename)
        app.logger.info(f"Output file will be: {output_file}")

        # Apply audio effect (if any)
        effect = request_data.get('effect_type', None)
        if effect:
            app.logger.info(f"Applying effect: {effect}")
            try:
                apply_audio_effect(input_file, output_file, effect)
                app.logger.info("Effect applied successfully")
            except Exception as e:
                app.logger.error(f"Error applying effect: {str(e)}")
                return jsonify({'error': f'Effect application failed: {str(e)}'}), 500
        else:
            # If no effect, just copy the file
            shutil.copy2(input_file, output_file)
            app.logger.info("No effect requested, file copied to output")

        # Clean up temp file
        try:
            os.remove(input_file)
            app.logger.info("Temporary file cleaned up")
        except Exception as e:
            app.logger.warning(f"Failed to clean up temp file: {str(e)}")

        app.logger.info("Processing completed successfully")
        return jsonify({
            'success': True,
            'message': 'Audio processed successfully',
            'filename': output_filename
        })

    except Exception as e:
        app.logger.error(f"Unexpected error in process_youtube: {str(e)}", exc_info=True)
        return jsonify({'error': f'Server error: {str(e)}'}), 500

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

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """Serve processed audio files."""
    try:
        output_dir = os.environ.get('OUTPUT_DIR', '/app/output')
        file_path = os.path.join(output_dir, filename)
        
        if not os.path.exists(file_path):
            app.logger.error(f"Audio file not found: {file_path}")
            return jsonify({'error': 'Audio file not found'}), 404
            
        app.logger.info(f"Serving audio file: {file_path}")
        
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Handle range requests for mobile browsers
        range_header = request.headers.get('Range', None)
        if range_header:
            app.logger.info(f"Range request received: {range_header}")
            byte1, byte2 = 0, None
            match = re.search('bytes=(\d+)-(\d*)', range_header)
            if match:
                groups = match.groups()
                if groups[0]:
                    byte1 = int(groups[0])
                if groups[1]:
                    byte2 = int(groups[1])

            if byte2 is None:
                byte2 = file_size - 1
            length = byte2 - byte1 + 1

            with open(file_path, 'rb') as f:
                f.seek(byte1)
                data = f.read(length)

            response = Response(
                data,
                206,
                mimetype='audio/mpeg',
                direct_passthrough=True,
            )
            response.headers.add('Content-Range', f'bytes {byte1}-{byte2}/{file_size}')
            response.headers.add('Accept-Ranges', 'bytes')
            response.headers.add('Content-Length', str(length))
            app.logger.info(f"Serving partial content: bytes {byte1}-{byte2}/{file_size}")
            return response
            
        # If no range request, serve entire file
        return send_file(
            file_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=filename
        )
    except Exception as e:
        app.logger.error(f"Error serving audio file: {str(e)}")
        app.logger.error(traceback.format_exc())
        return jsonify({'error': 'Failed to serve audio file'}), 500

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create temporary directories for processing
TEMP_DIR = os.environ.get('TEMP_DIR', tempfile.mkdtemp())
OUTPUT_DIR = os.path.join(TEMP_DIR, 'output')
os.makedirs(OUTPUT_DIR, exist_ok=True)

logger.info(f"Temporary directory created at: {TEMP_DIR}")
logger.info(f"Output directory created at: {OUTPUT_DIR}")

if __name__ == '__main__':
    # Validate cookies on startup
    if not validate_youtube_cookies():
        print("\n" + "="*80)
        print("⚠️  WARNING: YouTube Cookie Validation Failed!")
        print("="*80)
        print("The application will start, but YouTube downloads may not work.")
        print("This usually means one of:")
        print("1. The cookies.txt file is missing or invalid")
        print("2. The cookies have expired")
        print("3. YouTube is detecting the request as automated")
        print("\nTo fix this:")
        print("1. Run ./update_cookies.sh to refresh your cookies")
        print("2. Commit and push the new cookies.txt")
        print("3. Redeploy the application")
        print("="*80 + "\n")
    else:
        print("\n✅ YouTube cookies validated successfully! The application is ready.\n")
    
    port = int(os.environ.get('PORT', 5005))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
