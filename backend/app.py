from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
import os
import yt_dlp
import subprocess
import tempfile
import shutil
import logging
from datetime import datetime

app = Flask(__name__)

# Configure CORS to allow requests from your Vercel frontend
CORS(app, resources={
    r"/api/*": {
        "origins": [
            "https://moodi-fy.vercel.app",  # Production frontend
            "http://localhost:3000",        # Local development
            "http://localhost:5000"         # Local development
        ],
        "methods": ["GET", "POST", "OPTIONS"],
        "allow_headers": ["Content-Type"]
    }
})

# Rest of your Flask app code...
