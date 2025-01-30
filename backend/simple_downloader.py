import os
import re
import logging
import yt_dlp
from typing import Optional
from pydub import AudioSegment
from .youtube_auth import get_youtube_auth

logger = logging.getLogger(__name__)

class SimpleYouTubeDownloader:
    """A simpler, more direct approach to downloading YouTube audio."""
    
    def __init__(self):
        """Initialize the downloader with authentication."""
        self.auth = get_youtube_auth()
        
        # Configure yt-dlp options
        self.ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'nocheckcertificate': True
        }
    
    def extract_video_id(self, url: str) -> str:
        """Extract video ID from various YouTube URL formats."""
        if match := re.search(r'(?:v=|/v/|youtu\.be/)([^"&?/\s]{11})', url):
            return match.group(1)
        raise ValueError("Could not extract video ID from URL")

    def process(self, youtube_url: str, output_path: str) -> Optional[str]:
        """Main process to download audio from YouTube."""
        try:
            # Extract video ID
            video_id = self.extract_video_id(youtube_url)
            logger.info(f"Extracted video ID: {video_id}")
            
            # Create temporary directory for download
            temp_dir = os.path.join(os.path.dirname(output_path), 'temp')
            os.makedirs(temp_dir, exist_ok=True)
            
            try:
                # Set output template for yt-dlp
                self.ydl_opts['outtmpl'] = os.path.join(temp_dir, '%(title)s.%(ext)s')
                
                # Download with yt-dlp
                with yt_dlp.YoutubeDL(self.ydl_opts) as ydl:
                    # Get video info first
                    info = ydl.extract_info(youtube_url, download=False)
                    
                    # Download the video
                    ydl.download([youtube_url])
                    
                    # Get the output filename
                    output_file = os.path.join(temp_dir, f"{info['title']}.mp3")
                    
                    # Move to final destination
                    os.rename(output_file, output_path)
                    
                logger.info(f"Successfully downloaded and converted audio to: {output_path}")
                return output_path
                
            finally:
                # Clean up temp files
                for file in os.listdir(temp_dir):
                    try:
                        os.remove(os.path.join(temp_dir, file))
                    except OSError:
                        pass
                try:
                    os.rmdir(temp_dir)
                except OSError:
                    pass
            
        except Exception as e:
            logger.error(f"Error in download process: {str(e)}")
            if os.path.exists(output_path):
                os.remove(output_path)
            raise

def download_audio_simple(youtube_url: str, output_path: str) -> str:
    """Convenience function to download audio using SimpleYouTubeDownloader."""
    downloader = SimpleYouTubeDownloader()
    return downloader.process(youtube_url, output_path)
