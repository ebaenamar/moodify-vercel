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

## API Documentation

### POST /api/download
- **Purpose**: Process YouTube URL and apply audio effect
- **Headers**:
  - `Content-Type: application/json`
  - `X-Device-Info`: (optional) Device information
- **Request Body**:
```json
{
    "url": "YouTube URL",
    "effect_type": "slow_reverb|energetic|dark|cute"
}
```
- **Authentication**:
  - Uses cookies.txt for YouTube access
  - Handles age-restricted content
  - Manages authentication state
- **Response**:
```json
{
    "success": true,
    "filename": "processed_audio_file.mp3"
}
```
- **Error Response**:
```json
{
    "error": "Error message"
}
```
- **Status Codes**:
  - 200: Success
  - 400: Invalid request
  - 401: Authentication failed (cookie issues)
  - 500: Server error

### GET /api/audio/<filename>
- **Purpose**: Serve processed audio files
- **Headers**:
  - `Range`: (optional) For partial content requests
- **Response**: Audio file (MP3)
- **Error Response**: JSON with error message
- **Status Codes**:
  - 200: Full content
  - 206: Partial content
  - 404: File not found
  - 500: Server error

## Cookie Management Workflow

### Overview
The application uses a two-stage cookie management system:
1. Local cookie extraction and validation (Developer's machine)
2. Remote cookie usage (Render's Docker environment)

### Local Stage (Developer's Machine)
1. **Cookie Extraction**
   ```bash
   # Run update_cookies.sh locally
   ./update_cookies.sh
   ```
   - Extracts fresh cookies from local Chrome browser
   - Uses existing authenticated YouTube session
   - No need for password storage

2. **Validation Process**
   - Tests cookies with a sample video
   - Verifies authentication works
   - Creates backup of existing cookies

3. **Deployment**
   - Commits validated cookies to git
   - Pushes to repository
   - Maintains cookie security

### Remote Stage (Render Docker)
1. **Cookie Update**
   - Docker pulls latest code
   - Gets fresh cookies.txt
   - No browser automation needed

2. **Usage**
   - Backend uses cookies for downloads
   - Handles age-restricted content
   - Maintains authentication state

### Testing the Workflow

1. **Local Testing**
   ```bash
   # 1. Run update script
   ./update_cookies.sh

   # 2. Check git status
   git status

   # 3. Verify push
   git log --oneline
   ```

2. **Remote Verification**
   - Check Render logs
   - Try downloading age-restricted video
   - Monitor for authentication errors

### Security Considerations

1. **Cookie Protection**
   - Cookies only extracted locally
   - No credentials stored in cloud
   - Regular cookie rotation

2. **Access Control**
   - Limited to authenticated developers
   - Secure cookie transfer
   - Protected repository access

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
        { "src": "/api/(.*)", "dest": "https://moodi-fy.onrender.com/api/$1" }
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

## Troubleshooting Guide

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
