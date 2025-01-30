document.addEventListener('DOMContentLoaded', () => {
    const emojiContainer = document.querySelector('.emoji-container');
    const youtubeInput = document.getElementById('youtube-link');
    const loadingDiv = document.getElementById('loading');
    const audioClip = document.getElementById('audio-clip');
    const buttonContainer = document.querySelector('.button-container');
    const saveButton = document.getElementById('save-clip');
    const retryButton = document.getElementById('retry');
    const shareButton = document.getElementById('share');

    // Add API URL configuration at the top of the file
    const API_URL = 'https://moodi-fy.onrender.com';

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
    function showError(message) {
        const errorDiv = document.createElement('div');
        errorDiv.className = 'error-message';
        errorDiv.textContent = message;
        
        // Remove any existing error message
        const existingError = document.querySelector('.error-message');
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
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com|youtu\.be)\/.+/;
        return youtubeRegex.test(url);
    }

    // Create emoji buttons with tooltips
    vibes.forEach(vibe => {
        const emojiWrapper = document.createElement('div');
        emojiWrapper.classList.add('emoji-wrapper');
        
        const emoji = document.createElement('span');
        emoji.textContent = vibe.emoji;
        emoji.classList.add('emoji');
        
        const tooltip = document.createElement('span');
        tooltip.classList.add('tooltip');
        tooltip.textContent = vibe.name;
        
        emojiWrapper.appendChild(emoji);
        emojiWrapper.appendChild(tooltip);
        emojiContainer.appendChild(emojiWrapper);

        emoji.addEventListener('click', () => {
            document.querySelectorAll('.emoji').forEach(e => e.classList.remove('selected'));
            emoji.classList.add('selected');
            selectedVibe = vibe;
            
            // If we have a processed audio and select a new vibe, enable retry
            if (processedAudioUrl) {
                buttonContainer.classList.remove('hidden');
            }
        });
    });

    async function processYouTubeLink(url, vibeType) {
        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }

        if (!isValidYoutubeUrl(url)) {
            showError('Please enter a valid YouTube URL');
            return;
        }

        if (!vibeType) {
            showError('Please select a vibe first');
            return;
        }

        try {
            loadingDiv.classList.remove('hidden');
            buttonContainer.classList.add('hidden');
            audioClip.classList.add('hidden');

            const response = await fetch(`${API_URL}/api/transform`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    url: url,
                    effect_type: vibeType
                })
            });

            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    throw new Error(errorData.error || 'Failed to process audio');
                }
                throw new Error('Failed to process audio');
            }

            const data = await response.json();
            processedAudioUrl = data.audio_url;
            
            audioClip.src = processedAudioUrl;
            audioClip.classList.remove('hidden');
            buttonContainer.classList.remove('hidden');
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
            showError('Please select a vibe first');
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

    saveButton.addEventListener('click', async () => {
        if (processedAudioUrl) {
            try {
                const link = document.createElement('a');
                link.href = processedAudioUrl;
                link.download = 'transformed_audio.mp3';
                document.body.appendChild(link);
                link.click();
                document.body.removeChild(link);
            } catch (error) {
                showError('Failed to download audio');
            }
        }
    });

    shareButton.addEventListener('click', async () => {
        if (processedAudioUrl) {
            try {
                await navigator.clipboard.writeText(processedAudioUrl);
                alert('Audio URL copied to clipboard!');
            } catch (error) {
                showError('Failed to copy URL to clipboard');
            }
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