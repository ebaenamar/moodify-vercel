#!/usr/bin/env python3
import os
import subprocess
import shutil
from datetime import datetime

def filter_youtube_cookies(input_file, output_file):
    """Filter only the 30 most recent YouTube cookies from the input file"""
    with open(input_file, 'r') as infile:
        # Read all YouTube cookies
        youtube_cookies = []
        for line in infile:
            if not line.startswith('#') and ('.youtube.' in line):  # More specific matching
                fields = line.strip().split('\t')
                if len(fields) >= 5:
                    try:
                        expiry = int(fields[4])
                    except ValueError:
                        expiry = 0
                    youtube_cookies.append((expiry, line))

    # Sort by expiry time (most recent first) and take top 30
    youtube_cookies.sort(reverse=True)
    recent_cookies = youtube_cookies[:30]

    with open(output_file, 'w') as outfile:
        # Write header
        outfile.write("# Netscape HTTP Cookie File\n")
        outfile.write("# https://curl.haxx.se/rfc/cookie_spec.html\n")
        outfile.write("# This is a generated file!  Do not edit.\n")
        outfile.write(f"# Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Write the 30 most recent cookies
        for _, cookie_line in recent_cookies:
            outfile.write(cookie_line)

def main():
    # Get cookies from Chrome
    print("Getting cookies from Chrome...")
    temp_cookies = "temp_cookies.txt"
    youtube_cookies = "youtube_cookies.txt"
    
    try:
        subprocess.run([
            'yt-dlp',
            '--cookies-from-browser', 'chrome',
            '--cookies', temp_cookies,
            '--quiet',
            '--skip-download',
            'https://www.youtube.com/watch?v=dQw4w9WgXcQ'  # Use a specific video to avoid loading recommendations
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error getting cookies: {e}")
        return

    # Filter only recent YouTube cookies
    print("Filtering 30 most recent YouTube cookies...")
    filter_youtube_cookies(temp_cookies, youtube_cookies)
    os.remove(temp_cookies)  # Remove temporary file

    # Update cookies.txt
    print("Updating cookies.txt...")
    if os.path.exists('cookies.txt'):
        shutil.copy('cookies.txt', 'cookies.txt.backup')
    
    shutil.move(youtube_cookies, 'cookies.txt')
    os.chmod('cookies.txt', 0o644)
    
    print("Cookies updated successfully!")
    
    # Commit and push changes
    try:
        subprocess.run(['git', 'add', 'cookies.txt'], check=True)
        subprocess.run(['git', 'commit', '-m', 'Update YouTube cookies from Chrome'], check=True)
        subprocess.run(['git', 'push', 'origin', 'main'], check=True)
        print("Changes pushed to repository!")
    except subprocess.CalledProcessError as e:
        print(f"Error pushing changes: {e}")

if __name__ == "__main__":
    main()
