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
COPY cookies.txt /app/cookies.txt

# Create and set permissions for temp directory
RUN mkdir -p /app/temp/output && \
    chmod -R 777 /app/temp && \
    chmod 644 /app/cookies.txt

# Set environment variables
ENV TEMP_DIR=/app/temp
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1
ENV PORT=10000

# Update yt-dlp to latest version
RUN yt-dlp -U

# Expose port
EXPOSE ${PORT}

# Run the application with gunicorn
RUN pip install gunicorn
CMD gunicorn --bind 0.0.0.0:${PORT} --timeout 120 app:app
