#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Function to print with timestamp
log() {
    echo -e "${2:-$GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] $1${NC}"
}

# Function to check if a command exists
check_command() {
    if ! command -v $1 &> /dev/null; then
        log "Error: $1 is required but not installed." $RED
        exit 1
    fi
}

# Check required commands
check_command "yt-dlp"
check_command "git"

# Backup current cookies
if [ -f "cookies.txt" ]; then
    log "Backing up current cookies..." $YELLOW
    cp cookies.txt cookies.txt.backup.preview
fi

# Test video - Sabrina Carpenter - Espresso
TEST_VIDEO="eVli-tstM5E"

# Extract fresh cookies
log "Extracting fresh cookies for Preview deployment..." $YELLOW

# Try Firefox first
log "Trying Firefox..." $YELLOW
if yt-dlp --cookies-from-browser firefox --cookies cookies.txt "https://www.youtube.com/watch?v=$TEST_VIDEO"; then
    log "Successfully extracted cookies from Firefox" $GREEN
else
    log "Firefox failed, trying Chrome..." $YELLOW
    if ! yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=$TEST_VIDEO"; then
        log "Failed to extract cookies from Chrome." $RED
        if [ -f "cookies.txt.backup.preview" ]; then
            log "Restoring backup cookies..." $YELLOW
            mv cookies.txt.backup.preview cookies.txt
        fi
        exit 1
    fi
    log "Successfully extracted cookies from Chrome" $GREEN
fi

# Test the new cookies
log "Testing new cookies..." $YELLOW
if ! yt-dlp --cookies cookies.txt -F "https://www.youtube.com/watch?v=$TEST_VIDEO" > /dev/null; then
    log "Cookie test failed. The extracted cookies might not be valid." $RED
    if [ -f "cookies.txt.backup.preview" ]; then
        log "Restoring backup cookies..." $YELLOW
        mv cookies.txt.backup.preview cookies.txt
    fi
    exit 1
fi

# Check if we're in a git repository
log "Checking git remote..." $YELLOW
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    log "Not a git repository. Skipping git operations." $YELLOW
    exit 0
fi

# Commit the changes
log "Committing new cookies to Preview deployment..." $YELLOW
git add cookies.txt
git commit -m "chore: update YouTube cookies for Preview $(date '+%Y-%m-%d')"

# Push to the moodi-fy repository (Preview)
log "Pushing changes to Preview deployment..." $YELLOW
if ! git push origin main; then
    log "Failed to push changes to Preview." $RED
    exit 1
fi

log "Successfully updated cookies for Preview deployment! 🎉"
log "Don't forget to redeploy your Preview container on Render"
