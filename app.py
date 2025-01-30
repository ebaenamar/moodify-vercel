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

app = Flask(__name__)

# Configure CORS
CORS(app, 
     resources={
         r"/api/*": {
             "origins": ["https://moodify-vercel.vercel.app", "http://localhost:8080", "http://localhost:3000"],
             "methods": ["GET", "POST", "OPTIONS"],
             "allow_headers": ["Content-Type"],
             "expose_headers": ["Content-Type"],
             "supports_credentials": True
         }
     },
     allow_headers=["Content-Type"],
     expose_headers=["Content-Type"]
)

@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'https://moodify-vercel.vercel.app')
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
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }

def extract_video_id(url):
    """Extract the video ID from various YouTube URL formats."""
    patterns = [
        r'(?:v=|\/)([0-9A-Za-z_-]{11}).*',
        r'(?:embed\/)([0-9A-Za-z_-]{11})',
        r'(?:watch\?v=)([0-9A-Za-z_-]{11})'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def download_audio(url, output_path):
    """Download audio from YouTube using yt-dlp."""
    try:
        logger.info(f"Downloading audio from {url}")
        
        # Get cookies file path
        cookies_path = os.path.join(os.path.dirname(__file__), 'cookies.txt')
        if not os.path.exists(cookies_path):
            logger.warning("Cookies file not found, proceeding without authentication")
        
        # Configure yt-dlp options
        ydl_opts = {
            'format': 'bestaudio/best',
            'outtmpl': output_path,
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': False,
            'no_warnings': False,
            'verbose': True,
            'extract_flat': False,
            'force_generic_extractor': False,
            'nocheckcertificate': True,
            'noplaylist': True,
            'concurrent_fragment_downloads': 1,
            'http_headers': get_custom_headers(),
            'progress_hooks': [lambda d: logger.info(f"Download progress: {d.get('status', 'unknown')}")],
        }
        
        # Add cookies if available
        if os.path.exists(cookies_path):
            logger.info("Using authentication cookies")
            ydl_opts['cookiefile'] = cookies_path
        
        # Download with yt-dlp
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            logger.info("Starting download with yt-dlp")
            ydl.download([url])
        
        # Check for the output file
        mp3_path = output_path + '.mp3'
        if not os.path.exists(mp3_path):
            raise ValueError("Failed to create output file")
        
        logger.info("Download and conversion completed successfully")
        return mp3_path
            
    except Exception as e:
        logger.error(f"Error downloading audio: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Clean up any partial downloads
        try:
            mp3_path = output_path + '.mp3'
            if os.path.exists(mp3_path):
                os.remove(mp3_path)
        except Exception:
            pass
        
        if 'unavailable' in str(e).lower():
            raise ValueError("This video is unavailable. It might be private or removed.")
        elif 'copyright' in str(e).lower():
            raise ValueError("This video is not available due to copyright restrictions.")
        else:
            raise ValueError(f"Failed to download video: {str(e)}")

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
        
        # Generate unique filename
        temp_filename = f"{uuid.uuid4()}"
        download_path = os.path.join(TEMP_DIR, temp_filename)
        output_path = os.path.join(OUTPUT_DIR, f"{temp_filename}.mp3")

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

        return output_path

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

@app.route('/api/test', methods=['GET'])
def test():
    """Test endpoint to verify CORS is working"""
    return jsonify({
        'status': 'ok',
        'message': 'CORS is working'
    })

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'temp_dir': TEMP_DIR,
        'output_dir': OUTPUT_DIR
    }), 200

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
        output_path = process_youtube_audio(url, effect_type)
        
        if not os.path.exists(output_path):
            logger.error("Output file not found after processing")
            return jsonify({'error': 'Failed to create output file'}), 500
        
        logger.info(f"Sending processed file: {output_path}")
        # Return the processed file
        return send_file(
            output_path,
            mimetype='audio/mpeg',
            as_attachment=True,
            download_name=f"moodify_{secure_filename(effect_type)}.mp3"
        )

    except ValueError as e:
        logger.error(f"Value Error: {str(e)}")
        return jsonify({'error': str(e)}), 400
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        logger.error(traceback.format_exc())
        return jsonify({'error': 'An unexpected error occurred'}), 500

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5005))
    debug = os.environ.get('DEBUG', 'False').lower() == 'true'
    app.run(host='0.0.0.0', port=port, debug=debug)
