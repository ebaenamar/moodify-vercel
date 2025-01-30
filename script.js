document.addEventListener('DOMContentLoaded', () => {
    const emojiContainer = document.querySelector('.emoji-container');
    const youtubeInput = document.getElementById('youtube-link');
    const loadingDiv = document.getElementById('loading');
    const audioClip = document.getElementById('audio-clip');
    const buttonContainer = document.querySelector('.button-container');
    const saveButton = document.getElementById('save-clip');
    const retryButton = document.getElementById('retry');
    const shareButton = document.getElementById('share');

    // Keep the original API URL configuration
    const API_URL = window.location.hostname === 'localhost' 
        ? 'http://localhost:5005'
        : 'https://moodi-fy.onrender.com';

    const vibes = [
        { emoji: '🌙', type: 'slow_reverb', name: 'Dreamy' },
        { emoji: '🎉', type: 'energetic', name: 'Energetic' },
        { emoji: '🖤', type: 'dark', name: 'Dark' },
        { emoji: '💖', type: 'cute', name: 'Cute' },
        { emoji: '😎', type: 'cool', name: 'Cool' },
        { emoji: '🌈', type: 'happy', name: 'Happy' },
        { emoji: '🔥', type: 'intense', name: 'Intense' },
        { emoji: '🎶', type: 'melodic', name: 'Melodic' },
        { emoji: '🌿', type: 'chill', name: 'Chill' },
        { emoji: '💤', type: 'sleepy', name: 'Sleepy' }
    ];

    let selectedVibe = null;
    let processedAudioUrl = null;

    // Function to show error message
    function showError(message, type = 'error') {
        const errorDiv = document.createElement('div');
        errorDiv.className = type === 'error' ? 'error-message' : 'info-message';
        errorDiv.textContent = message;
        
        // Remove any existing error message
        const existingError = document.querySelector('.error-message, .info-message');
        if (existingError) {
            existingError.remove();
        }
        
        youtubeInput.parentNode.insertBefore(errorDiv, youtubeInput.nextSibling);
        
        // Remove error after 5 seconds
        setTimeout(() => {
            errorDiv.remove();
        }, 5000);
    }

    // Function to validate YouTube URL
    function isValidYoutubeUrl(url) {
        // More permissive regex that allows various YouTube URL formats and parameters
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/(?:watch\?v=|v\/|embed\/)|youtu\.be\/)[a-zA-Z0-9_-]{11}([&?].*)?$/;
        return youtubeRegex.test(url);
    }

    // Function to extract video ID from YouTube URL
    function getYoutubeVideoId(url) {
        const match = url.match(/(?:youtu\.be\/|youtube\.com\/(?:watch\?v=|v\/|embed\/))([a-zA-Z0-9_-]{11})/);
        return match ? match[1] : null;
    }

    // Function to get device-specific headers
    function getDeviceHeaders() {
        const defaultHeaders = {
            'Content-Type': 'application/json'
        };

        // Add mobile headers only if on a mobile device
        if (/iPhone|iPad|iPod|Android/i.test(navigator.userAgent)) {
            return {
                ...defaultHeaders,
                'User-Agent': navigator.userAgent,
                'X-Requested-With': 'XMLHttpRequest',
                'Accept': 'application/json',
                'Accept-Language': navigator.language || 'en',
                'X-Device-Type': /iPhone|iPad|iPod/.test(navigator.userAgent) ? 'ios' : 'android'
            };
        }

        return defaultHeaders;
    }

    // Function to handle mood selection
    function handleMoodSelection(emoji, vibe) {
        document.querySelectorAll('.emoji').forEach(e => e.classList.remove('selected'));
        emoji.classList.add('selected');
        selectedVibe = vibe;
        
        if (youtubeInput.value.trim()) {
            if (!isValidYoutubeUrl(youtubeInput.value.trim())) {
                showError('Please enter a valid YouTube URL');
            }
        } else {
            showError('Mood selected! Now paste a YouTube URL to transform your music.', 'info');
        }
    }

    // Create emoji buttons with tooltips
    vibes.forEach(vibe => {
        const emojiWrapper = document.createElement('div');
        emojiWrapper.classList.add('emoji-wrapper');
        
        const emoji = document.createElement('div');
        emoji.classList.add('emoji');
        emoji.textContent = vibe.emoji;
        
        const tooltip = document.createElement('div');
        tooltip.classList.add('tooltip');
        tooltip.textContent = vibe.name;
        
        emojiWrapper.appendChild(emoji);
        emojiWrapper.appendChild(tooltip);
        emojiContainer.appendChild(emojiWrapper);

        emoji.addEventListener('click', () => handleMoodSelection(emoji, vibe));
    });

    // Add cookie helper functions
    function showCookieInstructions() {
        const modal = document.createElement('div');
        modal.className = 'cookie-modal';
        modal.innerHTML = `
            <div class="cookie-modal-content">
                <h3>YouTube Authentication Required</h3>
                <p>To download videos, we need your YouTube cookies. Here's how to get them:</p>
                <ol>
                    <li>Go to <a href="https://www.youtube.com" target="_blank">YouTube.com</a> and make sure you're logged in</li>
                    <li>Right-click anywhere on the page and select "Inspect" or press F12</li>
                    <li>Go to the "Application" or "Storage" tab</li>
                    <li>Under "Cookies", click on "https://youtube.com"</li>
                    <li>Look for cookies named: VISITOR_INFO1_LIVE, LOGIN_INFO, SID, HSID, SSID, APISID, SAPISID, or __Secure-3PAPISID</li>
                    <li>Copy the values of these cookies below</li>
                </ol>
                <div class="cookie-inputs">
                    <input type="text" id="visitor-info" placeholder="VISITOR_INFO1_LIVE value">
                    <input type="text" id="login-info" placeholder="LOGIN_INFO value">
                    <input type="text" id="sid" placeholder="SID value">
                    <input type="text" id="hsid" placeholder="HSID value">
                </div>
                <div class="cookie-buttons">
                    <button onclick="saveCookies()">Save Cookies</button>
                    <button onclick="closeCookieModal()">Cancel</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
    }

    function saveCookies() {
        const cookieData = {
            VISITOR_INFO1_LIVE: document.getElementById('visitor-info').value,
            LOGIN_INFO: document.getElementById('login-info').value,
            SID: document.getElementById('sid').value,
            HSID: document.getElementById('hsid').value
        };
        
        // Save cookies to localStorage
        localStorage.setItem('youtube_cookies', JSON.stringify(cookieData));
        
        // Close modal
        closeCookieModal();
        
        // Show success message
        showSuccessMessage('YouTube cookies saved successfully!');
    }

    function closeCookieModal() {
        const modal = document.querySelector('.cookie-modal');
        if (modal) {
            modal.remove();
        }
    }

    function getStoredCookies() {
        const cookies = localStorage.getItem('youtube_cookies');
        return cookies ? JSON.parse(cookies) : null;
    }

    async function processYouTubeLink(url, vibeType) {
        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }

        try {
            // Check if we have stored cookies
            const storedCookies = getStoredCookies();
            if (!storedCookies) {
                showCookieInstructions();
                return;
            }

            loadingDiv.classList.remove('hidden');
            buttonContainer.classList.add('hidden');
            audioClip.classList.add('hidden');

            const response = await fetch(`${API_URL}/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getDeviceHeaders()
                },
                body: JSON.stringify({
                    url: url,
                    effect_type: vibeType,
                    cookies: storedCookies
                })
            });

            if (!response.ok) {
                const errorData = await response.json();
                if (errorData.error && errorData.error.includes('bot')) {
                    // If we get a bot detection error, ask for new cookies
                    localStorage.removeItem('youtube_cookies');
                    showCookieInstructions();
                    return;
                }
                throw new Error(errorData.error || 'Failed to process YouTube link');
            }

            // Get the audio blob directly from the response
            const blob = await response.blob();
            if (blob.size === 0) {
                throw new Error('Received empty audio file');
            }

            // Revoke the old URL if it exists
            if (processedAudioUrl) {
                URL.revokeObjectURL(processedAudioUrl);
            }

            // Create a new blob URL
            processedAudioUrl = URL.createObjectURL(blob);
            
            audioClip.src = processedAudioUrl;
            audioClip.classList.remove('hidden');
            buttonContainer.classList.remove('hidden');
            
            // Start playing automatically
            try {
                await audioClip.play();
            } catch (playError) {
                console.log('Auto-play failed:', playError);
            }
            
        } catch (error) {
            showError(error.message || 'An error occurred while processing your request');
        } finally {
            loadingDiv.classList.add('hidden');
        }
    }

    youtubeInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter' && selectedVibe) {
            const url = youtubeInput.value.trim();
            if (url) {
                processYouTubeLink(url, selectedVibe.type);
            } else {
                showError('Please enter a YouTube URL');
            }
        } else if (e.key === 'Enter' && !selectedVibe) {
            showError('Please select a mood first! Click on one of the emojis above.');
        }
    });

    retryButton.addEventListener('click', () => {
        youtubeInput.value = '';
        audioClip.src = '';
        audioClip.classList.add('hidden');
        buttonContainer.classList.add('hidden');
        document.querySelectorAll('.emoji').forEach(e => e.classList.remove('selected'));
        selectedVibe = null;
        processedAudioUrl = null;
    });

    saveButton.addEventListener('click', () => {
        if (processedAudioUrl) {
            const a = document.createElement('a');
            a.href = processedAudioUrl;
            a.download = `moodify_${selectedVibe.type}.mp3`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
        }
    });

    shareButton.addEventListener('click', () => {
        if (processedAudioUrl) {
            // Implement sharing functionality here
            alert('Sharing coming soon!');
        }
    });

    // Add click handlers for song titles
    document.querySelectorAll('.song-title').forEach(songTitle => {
        songTitle.addEventListener('click', (e) => {
            e.preventDefault();
            const youtubeLink = songTitle.dataset.youtubeLink;
            youtubeInput.value = youtubeLink;
            
            // Show a brief "Copied!" message
            const tooltip = songTitle.querySelector('.copy-tooltip');
            const originalText = tooltip.textContent;
            tooltip.textContent = 'Copied!';
            setTimeout(() => {
                tooltip.textContent = originalText;
            }, 2000);
        });
    });
});