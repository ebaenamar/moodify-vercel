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
        const youtubeRegex = /^(https?:\/\/)?(www\.)?(youtube\.com\/watch\?v=|youtu\.be\/)[a-zA-Z0-9_-]{11}$/;
        return youtubeRegex.test(url);
    }

    // Function to extract video ID from YouTube URL
    function getYoutubeVideoId(url) {
        const match = url.match(/(?:youtu\.be\/|youtube\.com\/watch\?v=)([a-zA-Z0-9_-]{11})/);
        return match ? match[1] : null;
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

    async function processYouTubeLink(url, vibeType) {
        if (!url) {
            showError('Please enter a YouTube URL');
            return;
        }

        if (!isValidYoutubeUrl(url)) {
            showError('Please enter a valid YouTube URL (e.g., https://youtube.com/watch?v=... or https://youtu.be/...)');
            return;
        }

        if (!vibeType) {
            showError('Please select a mood first! Click on one of the emojis above.');
            return;
        }

        try {
            // Test CORS first (keeping original functionality)
            try {
                const testResponse = await fetch(`${API_URL}/api/test`, {
                    method: 'GET',
                    headers: {
                        'Content-Type': 'application/json'
                    }
                });
                
                if (!testResponse.ok) {
                    throw new Error('CORS test failed');
                }
                
                const testData = await testResponse.json();
                console.log('CORS test successful:', testData);
            } catch (corsError) {
                console.error('CORS test failed:', corsError);
                throw new Error('Unable to connect to the server. Please try again later.');
            }

            loadingDiv.classList.remove('hidden');
            buttonContainer.classList.add('hidden');
            audioClip.classList.add('hidden');

            const response = await fetch(`${API_URL}/api/transform`, {  
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({
                    url: url,
                    effect_type: vibeType  
                })
            });

            let errorMessage = 'Failed to process audio';
            if (!response.ok) {
                const contentType = response.headers.get('content-type');
                if (contentType && contentType.includes('application/json')) {
                    const errorData = await response.json();
                    errorMessage = errorData.error || errorMessage;
                } else {
                    const textError = await response.text();
                    console.error('Server error:', textError);
                }
                throw new Error(errorMessage);
            }

            const data = await response.json();
            processedAudioUrl = data.audio_url;
            
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