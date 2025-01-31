# Moodify Developer Documentation

## System Architecture

### Overview
Moodify is a web application that transforms YouTube audio using various effects. It's built with:
- Frontend: Vanilla JavaScript, HTML5, CSS3
- Backend: Python/Flask
- Deployment: Vercel (frontend) & Render (backend)

```
[Frontend]              [Backend]               [External]
   UI  ----HTTP/JSON--->  API  ----HTTP/Auth--->  YouTube
   ^                      |
   |                     v
   |                [Audio Processing]
   |                     |
   <-----Audio Stream----+
```

## Core Components

### 1. Frontend (`script.js`)

#### URL Processing
```javascript
// Main URL handling flow
url -> validateUrl() -> extractVideoId() -> sendToBackend()
```

Key functions:
- `isValidYoutubeUrl()`: Validates YouTube URL format
- `getYoutubeVideoId()`: Extracts video ID from URL
- `handleMoodSelection()`: Manages mood selection and triggers processing

#### Audio Handling
```javascript
// Audio processing flow
response -> createBlob() -> createAudioPlayer() -> setupControls()
```

Important considerations:
- Uses `Range` requests for mobile streaming
- Handles partial content responses
- Manages audio player state

### 2. Backend (`app.py`)

#### Request Flow
```python
request -> validate_request() -> download_audio() -> apply_effect() -> stream_response()
```

Key endpoints:
- `POST /api/download`: Initiates download and processing
- `GET /api/audio/<filename>`: Streams processed audio

#### YouTube Integration
- Uses cookies for authentication
- Handles age-restricted content
- Manages download streams

### 3. Audio Processing (`transform.py`)

#### Effect Pipeline
```python
audio -> load() -> apply_effect() -> export()
```

Available effects:
- `slow_reverb`: Time stretch + reverb
- `energetic`: EQ boost + compression
- `dark`: Low-end boost + atmosphere
- `cute`: High-end enhance + pitch

## Authentication System

### Cookie Management
```bash
# Update cycle
update_cookies.sh -> validate_cookies.py -> cookies.txt
```

Key components:
- `update_cookies.sh`: Automated cookie updater
- `validate_cookies.py`: Cookie validator
- `cookies.txt`: Cookie storage

## Error Handling

### Frontend Errors
```javascript
try {
    // Operation
} catch (error) {
    handleError(error);
    showUserFriendlyMessage();
    logToSystem(error);
}
```

### Backend Errors
```python
try:
    # Operation
except YouTubeError:
    handle_youtube_error()
except ProcessingError:
    handle_processing_error()
finally:
    cleanup_resources()
```

## Mobile Support

### Range Requests
```http
GET /api/audio/file.mp3
Range: bytes=0-1024
```

Response:
```http
HTTP/1.1 206 Partial Content
Content-Range: bytes 0-1024/4096
```

### CORS Configuration
```python
CORS_ORIGINS = [
    "https://moodi-fy.vercel.app",
    "capacitor://*",
    "ionic://*"
]
```

## Development Setup

### Prerequisites
```bash
# Python dependencies
pip install -r requirements.txt

# Environment setup
export YOUTUBE_COOKIES_PATH="./cookies.txt"
export TEMP_DIR="./temp"
```

### Local Development
```bash
# Start backend (http://localhost:5005)
python app.py

# Serve frontend (http://localhost:3000)
python -m http.server 3000
```

## Deployment

### Frontend (Vercel)
```bash
# Configuration
vercel.json:
{
    "routes": [
        { "src": "/api/(.*)", "dest": "https://moodify-vercel.onrender.com/api/$1" }
    ]
}
```

### Backend (Render)
```bash
# Build command
pip install -r requirements.txt

# Start command
gunicorn app:app
```

## Performance Optimization

### Frontend
- Blob URL management
- Audio element cleanup
- Memory leak prevention

### Backend
- Temporary file cleanup
- Stream buffer management
- Process pool for audio processing

## Security Measures

### Request Validation
```python
def validate_request(request):
    validate_origin()
    validate_content_type()
    validate_url()
    validate_effect_type()
```

### File Security
```python
def secure_filename(filename):
    sanitize_input()
    check_directory_traversal()
    validate_extension()
```

## Debugging Guide

### Frontend Issues
1. Network tab in DevTools
   - Check request headers
   - Verify response status
   - Monitor data transfer

2. Console debugging
   ```javascript
   console.log('Request:', {
       url: url,
       headers: headers,
       body: body
   });
   ```

### Backend Issues
1. Log checking
   ```bash
   tail -f app.log
   ```

2. Cookie validation
   ```bash
   python validate_cookies.py --verbose
   ```

## Common Problems & Solutions

### 1. "Failed to Fetch" Errors
- Check CORS configuration
- Verify API endpoints
- Test network connection

### 2. Audio Processing Failures
- Verify YouTube URL accessibility
- Check disk space
- Monitor memory usage

### 3. Mobile Streaming Issues
- Enable range requests
- Check content-type headers
- Verify partial content handling
