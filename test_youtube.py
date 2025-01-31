#!/usr/bin/env python3
import yt_dlp
import sys
import json

def get_custom_headers():
    """Get custom headers for YouTube requests."""
    return {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-us,en;q=0.5',
        'Sec-Fetch-Mode': 'navigate'
    }

def test_youtube_url(url, browser='chrome', profile=None, cookies_file=None):
    """Test if we can access a YouTube video with different cookie methods."""
    results = []
    
    # Method 1: Direct browser cookies
    if browser:
        print(f"\nTesting with {browser.title()} browser cookies...")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'nocheckcertificate': True,
            'noplaylist': True,
            'cookies_from_browser': (browser, profile) if profile else browser,
            'http_headers': get_custom_headers()
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                results.append({
                    'method': f'{browser.title()} browser cookies',
                    'success': True,
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'is_private': info.get('is_private', False),
                    'age_limit': info.get('age_limit', 0)
                })
        except Exception as e:
            results.append({
                'method': f'{browser.title()} browser cookies',
                'success': False,
                'error': str(e)
            })
    
    # Method 2: Cookies file
    if cookies_file:
        print(f"\nTesting with cookies file: {cookies_file}...")
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': True,
            'nocheckcertificate': True,
            'noplaylist': True,
            'cookiefile': cookies_file,
            'http_headers': get_custom_headers()
        }
        
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                results.append({
                    'method': 'Cookies file',
                    'success': True,
                    'title': info.get('title'),
                    'duration': info.get('duration'),
                    'is_private': info.get('is_private', False),
                    'age_limit': info.get('age_limit', 0)
                })
        except Exception as e:
            results.append({
                'method': 'Cookies file',
                'success': False,
                'error': str(e)
            })
    
    # Print results
    print("\nResults:")
    print("-" * 50)
    for result in results:
        print(f"\nMethod: {result['method']}")
        if result['success']:
            print("✅ Success!")
            print(f"Title: {result.get('title')}")
            print(f"Duration: {result.get('duration')}s")
            print(f"Age limit: {result.get('age_limit')}+")
            print(f"Private: {'Yes' if result.get('is_private') else 'No'}")
        else:
            print("❌ Failed!")
            print(f"Error: {result.get('error')}")
    
    # Return True if any method succeeded
    return any(r['success'] for r in results)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python test_youtube.py VIDEO_URL [browser_profile] [cookies_file]")
        print("\nExample:")
        print("python test_youtube.py https://youtube.com/watch?v=xxx")
        print("python test_youtube.py https://youtube.com/watch?v=xxx 'Profile 1'")
        print("python test_youtube.py https://youtube.com/watch?v=xxx '' cookies.txt")
        sys.exit(1)
    
    url = sys.argv[1]
    profile = sys.argv[2] if len(sys.argv) > 2 else None
    cookies_file = sys.argv[3] if len(sys.argv) > 3 else 'cookies.txt'
    
    if not test_youtube_url(url, profile=profile, cookies_file=cookies_file):
        sys.exit(1)  # Exit with error if all methods failed
