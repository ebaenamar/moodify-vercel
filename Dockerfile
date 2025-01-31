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

# Verify cookie file exists and has correct permissions
RUN ls -l cookies.txt || (echo "cookies.txt not found!" && exit 1) && \
    chown app:app cookies.txt && \
    chmod 644 cookies.txt && \
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

# Update yt-dlp to latest version
RUN yt-dlp -U

# Switch to app user for validation and running
USER app

# Test cookie file access
RUN echo "Testing cookie file access..." && \
    cat cookies.txt > /dev/null && \
    echo "Cookie file is readable!"

# Validate cookies during build
RUN chmod +x validate_cookies.py && \
    python3 validate_cookies.py

# Expose port
EXPOSE ${PORT}

# Run the application with gunicorn
RUN pip install --user gunicorn
CMD python3 -m gunicorn --bind 0.0.0.0:${PORT} --timeout 120 app:app
