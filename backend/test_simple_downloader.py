import os
import tempfile
import unittest
from simple_downloader import SimpleYouTubeDownloader

class TestSimpleYouTubeDownloader(unittest.TestCase):
    def setUp(self):
        self.downloader = SimpleYouTubeDownloader()

    def test_video_id_extraction(self):
        """Test video ID extraction from various URL formats."""
        test_urls = [
            ('https://www.youtube.com/watch?v=dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
            ('https://youtu.be/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
            ('https://www.youtube.com/v/dQw4w9WgXcQ', 'dQw4w9WgXcQ'),
        ]
        for url, expected_id in test_urls:
            with self.subTest(url=url):
                video_id = self.downloader.extract_video_id(url)
                self.assertEqual(video_id, expected_id)

    def test_full_download(self):
        """Test complete download process."""
        test_video_url = 'https://youtu.be/vOb3id28dVA'
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            try:
                output_path = self.downloader.process(
                    test_video_url,
                    temp_file.name
                )
                self.assertTrue(os.path.exists(output_path))
                self.assertGreater(os.path.getsize(output_path), 0)
            finally:
                if os.path.exists(temp_file.name):
                    os.unlink(temp_file.name)

if __name__ == '__main__':
    unittest.main()
