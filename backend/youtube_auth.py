import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

class YouTubeAuth:
    """Handle YouTube OAuth2 authentication."""
    
    def __init__(self, client_secrets_file: str = 'config/client_secret.json',
                 token_file: str = 'config/youtube_token.json'):
        """Initialize the YouTube auth handler.
        
        Args:
            client_secrets_file: Path to the OAuth 2.0 client secrets file
            token_file: Path to store/retrieve the token
        """
        self.client_secrets_file = client_secrets_file
        self.token_file = token_file
        self.scopes = [
            'https://www.googleapis.com/auth/youtube.readonly',
            'https://www.googleapis.com/auth/youtube.force-ssl'
        ]
        
    def get_credentials(self) -> Credentials:
        """Get valid user credentials from storage or create new ones.
        
        Returns:
            Valid credentials object for YouTube API access
        """
        credentials = None
        
        # Check if we have valid stored credentials
        if os.path.exists(self.token_file):
            try:
                credentials = Credentials.from_authorized_user_file(
                    self.token_file, self.scopes)
            except Exception as e:
                print(f"Error loading stored credentials: {e}")
                
        # If there are no (valid) credentials available, let the user log in
        if not credentials or not credentials.valid:
            if credentials and credentials.expired and credentials.refresh_token:
                try:
                    credentials.refresh(Request())
                except Exception as e:
                    print(f"Error refreshing credentials: {e}")
                    credentials = None
                    
            if not credentials:
                if not os.path.exists(self.client_secrets_file):
                    raise FileNotFoundError(
                        f"Client secrets file not found at {self.client_secrets_file}. "
                        "Please download it from Google Cloud Console and place it in the config directory."
                    )
                
                flow = InstalledAppFlow.from_client_secrets_file(
                    self.client_secrets_file, self.scopes)
                credentials = flow.run_local_server(port=0)
            
            # Save the credentials for the next run
            with open(self.token_file, 'w') as token:
                token.write(credentials.to_json())
                
        return credentials

def get_youtube_auth() -> YouTubeAuth:
    """Convenience function to get a YouTubeAuth instance."""
    return YouTubeAuth()
