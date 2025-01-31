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

    async function getYoutubeCookies() {
        try {
            // Create an iframe to access youtube.com cookies
            const iframe = document.createElement('iframe');
            iframe.style.display = 'none';
            iframe.src = 'https://www.youtube.com';
            document.body.appendChild(iframe);

            // Wait for iframe to load
            await new Promise(resolve => iframe.onload = resolve);

            // Get cookies using document.cookie from the iframe
            const cookies = iframe.contentWindow.document.cookie;
            
            // Clean up
            document.body.removeChild(iframe);
            
            return cookies;
        } catch (error) {
            console.error('Error getting YouTube cookies:', error);
            return null;
        }
    }

    async function processYouTubeLink(url, vibeType) {
        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }

        try {
            loadingDiv.classList.remove('hidden');
            buttonContainer.classList.add('hidden');
            audioClip.classList.add('hidden');

            console.log(`Making request to ${API_URL}/api/download with effect: ${vibeType}`);
            const response = await fetch(`${API_URL}/api/download`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    ...getDeviceHeaders()
                },
                body: JSON.stringify({
                    url: url,
                    effect_type: vibeType
                })
            });

            console.log('Response status:', response.status);
            console.log('Response headers:', Object.fromEntries([...response.headers]));

            if (!response.ok) {
                const errorData = await response.json().catch(e => ({ error: 'Failed to parse error response' }));
                console.error('Error response:', errorData);
                throw new Error(errorData.error || 'Failed to process YouTube link');
            }

            const data = await response.json();
            console.log('Response data:', data);

            if (!data.success) {
                throw new Error(data.error || 'Failed to process audio');
            }

            console.log(`Fetching audio from ${API_URL}/api/audio/${data.filename}`);
            const audioResponse = await fetch(`${API_URL}/api/audio/${data.filename}`);
            
            console.log('Audio response status:', audioResponse.status);
            console.log('Audio response headers:', Object.fromEntries([...audioResponse.headers]));

            if (!audioResponse.ok) {
                const audioError = await audioResponse.text().catch(() => 'Failed to fetch audio');
                console.error('Audio error:', audioError);
                throw new Error('Failed to fetch processed audio');
            }

            // Get the audio blob
            const blob = await audioResponse.blob();
            console.log('Audio blob size:', blob.size, 'type:', blob.type);

            if (blob.size === 0) {
                throw new Error('Received empty audio file');
            }

            // Check if it's actually an audio file
            if (!blob.type.startsWith('audio/')) {
                throw new Error('Invalid audio file received');
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
                console.error('Auto-play failed:', playError);
            }
            
        } catch (error) {
            console.error('Processing error:', error);
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