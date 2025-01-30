from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import json
import boto3
from botocore.exceptions import ClientError
import logging
import re
from urllib.parse import urlparse

app = Flask(__name__)
CORS(app)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize AWS clients (you'll need to set these environment variables in Vercel)
s3_client = boto3.client(
    's3',
    aws_access_key_id=os.environ.get('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.environ.get('AWS_SECRET_ACCESS_KEY')
)

BUCKET_NAME = os.environ.get('S3_BUCKET_NAME')

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

@app.route('/api/transform', methods=['POST'])
def transform_audio():
    try:
        data = request.get_json()
        url = data.get('url')
        effect_type = data.get('effect_type', 'slow_reverb')

        if not url:
            return jsonify({'error': 'No URL provided'}), 400

        # Extract video ID and validate
        video_id = extract_video_id(url)
        if not video_id:
            return jsonify({'error': 'Invalid YouTube URL'}), 400

        # Instead of processing directly, we'll create a processing job
        job_id = f"job_{video_id}_{effect_type}"
        
        # Store job in SQS or similar queue service
        # For now, we'll return a job ID that the frontend can poll
        response = {
            'job_id': job_id,
            'status': 'processing',
            'message': 'Your audio is being processed. Please check back in a few moments.'
        }
        
        return jsonify(response)

    except Exception as e:
        logger.error(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status/<job_id>', methods=['GET'])
def check_status(job_id):
    try:
        # Here you would check the actual job status from your queue/database
        # For now, we'll simulate a response
        return jsonify({
            'job_id': job_id,
            'status': 'processing',
            'message': 'Your audio is still being processed.'
        })

    except Exception as e:
        logger.error(f"Error checking status: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({'status': 'healthy'})
