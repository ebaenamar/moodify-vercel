FROM python:3.9-slim

# Install system dependencies including FFmpeg
RUN apt-get update && \
    apt-get install -y ffmpeg git wget python3-dev build-essential dos2unix && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create app user
RUN useradd -m -d /home/app app && \
    chown -R app:app /home/app

# Create necessary directories with proper permissions
RUN mkdir -p /app/temp/output && \
    mkdir -p /app/output && \
    chown -R app:app /app && \
    chmod -R 755 /app

# Copy application code
COPY . .

# Set up file permissions while still root
RUN ls -l cookies.txt || (echo "cookies.txt not found!" && exit 1) && \
    # Convert line endings and remove any macOS attributes
    dos2unix cookies.txt && \
    chown app:app cookies.txt && \
    chmod 644 cookies.txt && \
    chmod +x validate_cookies.py && \
    # Print cookie file info for debugging
    echo "Cookie file details:" && \
    ls -l cookies.txt && \
    head -n 3 cookies.txt

# Set environment variables
ENV TEMP_DIR=/app/temp
ENV OUTPUT_DIR=/app/output
ENV DEBUG=False
ENV PYTHONUNBUFFERED=1
ENV PORT=10000
ENV RENDER=true

# Update yt-dlp to latest version
RUN yt-dlp -U

# Switch to app user for validation and running
USER app

# Test cookie file access
RUN echo "Testing cookie file access..." && \
    cat cookies.txt > /dev/null && \
    echo "Cookie file is readable!"

# Only check if cookie file exists and is not empty during build
ENV SKIP_DOWNLOAD_TEST=true
RUN python3 validate_cookies.py || (echo "Cookie file check failed" && exit 1)

# Reset for runtime
ENV SKIP_DOWNLOAD_TEST=false

# Expose port
EXPOSE ${PORT}

# Run the application with gunicorn
RUN pip install --user gunicorn
CMD python3 -m gunicorn --bind 0.0.0.0:${PORT} --timeout 120 app:app
