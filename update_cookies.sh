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
    cp cookies.txt cookies.txt.backup
fi

# Test video ID (a very popular video that's unlikely to be taken down)
TEST_VIDEO="dQw4w9WgXcQ"

# Extract fresh cookies
log "Extracting fresh cookies from Chrome..." $YELLOW
if ! yt-dlp --cookies-from-browser chrome --cookies cookies.txt "https://www.youtube.com/watch?v=$TEST_VIDEO"; then
    log "Failed to extract cookies from Chrome." $RED
    if [ -f "cookies.txt.backup" ]; then
        log "Restoring backup cookies..." $YELLOW
        mv cookies.txt.backup cookies.txt
    fi
    exit 1
fi

# Test the new cookies
log "Testing new cookies..." $YELLOW
if ! yt-dlp --cookies cookies.txt -F "https://www.youtube.com/watch?v=$TEST_VIDEO" > /dev/null; then
    log "Cookie test failed. The extracted cookies might not be valid." $RED
    if [ -f "cookies.txt.backup" ]; then
        log "Restoring backup cookies..." $YELLOW
        mv cookies.txt.backup cookies.txt
    fi
    exit 1
fi

# Check if there are any changes to cookies.txt
if git diff --quiet cookies.txt; then
    log "No changes detected in cookies.txt" $YELLOW
    rm -f cookies.txt.backup
    exit 0
fi

# Commit and push changes
log "Committing new cookies..." $YELLOW
if ! git add cookies.txt; then
    log "Failed to stage cookies.txt" $RED
    exit 1
fi

if ! git commit -m "chore: update YouTube cookies $(date '+%Y-%m-%d')

- Extract fresh cookies from Chrome browser
- Test cookies with a sample video
- Update cookies.txt for Docker deployment"; then
    log "Failed to commit changes" $RED
    exit 1
fi

log "Pushing changes..." $YELLOW
if ! git push; then
    log "Failed to push changes" $RED
    exit 1
fi

# Clean up
rm -f cookies.txt.backup

log "Successfully updated cookies! 🎉"
log "Don't forget to redeploy your container on Render"
