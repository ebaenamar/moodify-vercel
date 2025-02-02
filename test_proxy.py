#!/usr/bin/env python3
import requests
import yt_dlp
import logging
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TEST_VIDEO = "https://www.youtube.com/watch?v=eVli-tstM5E"

def test_proxy(proxy):
    try:
        start = time.time()
        # Test basic connectivity
        response = requests.get('https://www.youtube.com', 
                              proxies={'http': proxy, 'https': proxy},
                              timeout=10)
        
        # Test video info extraction
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'proxy': proxy
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(TEST_VIDEO, download=False)
        
        elapsed = time.time() - start
        return {
            'proxy': proxy,
            'working': True,
            'speed': elapsed,
            'status': response.status_code,
            'title': info.get('title', 'Unknown')
        }
    except Exception as e:
        return {
            'proxy': proxy,
            'working': False,
            'error': str(e)
        }

def get_free_proxies():
    """Get free proxies from multiple sources"""
    proxies = set()
    
    # Try ProxyScrape API
    try:
        r = requests.get('https://api.proxyscrape.com/v2/?request=getproxies&protocol=http&timeout=10000&country=all&ssl=all&anonymity=all')
        if r.status_code == 200:
            proxies.update(f'http://{p.strip()}' for p in r.text.split() if p.strip())
    except Exception as e:
        logger.warning(f"Failed to get proxies from ProxyScrape: {e}")
    
    # Try Proxy-List API
    try:
        r = requests.get('https://www.proxy-list.download/api/v1/get?type=https')
        if r.status_code == 200:
            proxies.update(f'http://{p.strip()}' for p in r.text.split() if p.strip())
    except Exception as e:
        logger.warning(f"Failed to get proxies from Proxy-List: {e}")
    
    return list(proxies)

def main():
    logger.info("Fetching free proxies...")
    proxies = get_free_proxies()
    logger.info(f"Found {len(proxies)} proxies to test")
    
    working_proxies = []
    with ThreadPoolExecutor(max_workers=10) as executor:
        future_to_proxy = {executor.submit(test_proxy, proxy): proxy for proxy in proxies}
        for future in as_completed(future_to_proxy):
            result = future.result()
            if result['working']:
                working_proxies.append(result)
                logger.info(f"Found working proxy: {result['proxy']}")
                logger.info(f"Speed: {result['speed']:.2f}s")
                logger.info(f"Video title: {result.get('title', 'Unknown')}")
                
    logger.info("\nSummary of working proxies:")
    for proxy in sorted(working_proxies, key=lambda x: x['speed']):
        logger.info(f"Proxy: {proxy['proxy']}")
        logger.info(f"Speed: {proxy['speed']:.2f}s")
        logger.info("---")

if __name__ == "__main__":
    main()
