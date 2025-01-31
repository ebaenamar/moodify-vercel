FROM python:3.9-slim

# Install system dependencies including FFmpeg and Chrome
RUN apt-get update && \
    apt-get install -y ffmpeg git wget python3-dev build-essential chromium chromium-driver && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code and cookies
COPY . .

# Create necessary directories with proper permissions
RUN mkdir -p /app/temp/output && \
    mkdir -p /app/output && \
    touch /app/cookies.txt && \
    chmod -R 777 /app/temp && \
    chmod -R 777 /app/output && \
    chmod 666 /app/cookies.txt

# Set environment variables
ENV TEMP_DIR=/app/temp
ENV OUTPUT_DIR=/app/output
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV CHROME_PATH=/usr/bin/chromium
ENV CHROME_DRIVER_PATH=/usr/bin/chromedriver

# Update yt-dlp to latest version
RUN yt-dlp -U

# Expose port
EXPOSE ${PORT}

# Run the application with gunicorn
RUN pip install gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT} --timeout 120 app:app
