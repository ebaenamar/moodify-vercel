FROM python:3.9-slim

# Install system dependencies including FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg git wget python3-dev build-essential && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and cookies
COPY . .

# Verify cookie file exists and has correct permissions
RUN ls -l cookies.txt || (echo "cookies.txt not found!" && exit 1)

# Create necessary directories with proper permissions
RUN mkdir -p /app/temp/output && \
    mkdir -p /app/output && \
    chmod -R 777 /app/temp && \
    chmod -R 777 /app/output && \
    chmod 644 /app/cookies.txt

# Set environment variables
ENV TEMP_DIR=/app/temp
ENV OUTPUT_DIR=/app/output
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Update yt-dlp to latest version
RUN yt-dlp -U

# Create and run cookie validation script
RUN echo '#!/usr/bin/env python3\n\
import sys\n\
from app import validate_youtube_cookies\n\
\n\
if not validate_youtube_cookies():\n\
    print("\\n❌ ERROR: YouTube cookie validation failed!")\n\
    print("The cookies.txt file exists but is not working in the Docker environment.")\n\
    print("Please run ./update_cookies.sh to refresh your cookies and try again.\\n")\n\
    sys.exit(1)\n\
else:\n\
    print("\\n✅ YouTube cookies validated successfully in Docker!\\n")\n\
' > validate_cookies.py && \
    chmod +x validate_cookies.py && \
    python3 validate_cookies.py

# Expose port
EXPOSE ${PORT}

# Run the application with gunicorn
RUN pip install gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT} --timeout 120 app:app
