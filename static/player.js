// YouTube Player and Gesture Control JavaScript

let player;
let socket;
let webcamStream;

// Initialize YouTube Player API
function onYouTubeIframeAPIReady() {
    player = new YT.Player('player', {
        height: '100%',
        width: '100%',
        videoId: videoId,
        playerVars: {
            'playsinline': 1,
            'modestbranding': 1,
            'rel': 0
        },
        events: {
            'onReady': onPlayerReady,
            'onStateChange': onPlayerStateChange
        }
    });
}

function onPlayerReady(event) {
    console.log('YouTube player ready');
    initializeWebcam();
    initializeSocket();
}

function onPlayerStateChange(event) {
    console.log('Player state changed:', event.data);
}

// Extract video ID from URL
function getVideoIdFromUrl(url) {
    const regExp = /^.*(youtu.be\/|v\/|u\/\w\/|embed\/|watch\?v=|&v=)([^#&?]*).*/;
    const match = url.match(regExp);
    return (match && match[2].length == 11) ? match[2] : null;
}

// Initialize webcam stream
async function initializeWebcam() {
    try {
        const videoElement = document.getElementById('webcam');
        const overlayElement = document.getElementById('overlay');

        webcamStream = await navigator.mediaDevices.getUserMedia({
            video: { width: 640, height: 480 }
        });

        videoElement.srcObject = webcamStream;

        // Start sending video stream to backend
        socket.emit('start_stream');
    } catch (error) {
        console.error('Error accessing webcam:', error);
        alert('Unable to access webcam. Please ensure camera permissions are granted.');
    }
}

// Initialize WebSocket connection
function initializeSocket() {
    socket = io();

    socket.on('connect', () => {
        console.log('Connected to server');
    });

    socket.on('disconnect', () => {
        console.log('Disconnected from server');
    });

    // Handle gesture actions from backend
    socket.on('gesture_action', (data) => {
        handleGestureAction(data.action, data.gesture);
    });

    // Handle video frames from backend (for overlay)
    socket.on('video_frame', (data) => {
        // Optional: Display processed frame with landmarks
        // This would require additional canvas drawing
    });
}

// Handle gesture actions
function handleGestureAction(action, gesture) {
    console.log('Received action:', action, 'from gesture:', gesture);

    // Show feedback message
    showFeedback(getFeedbackMessage(action));

    // Execute YouTube player action
    switch (action) {
        case 'play':
            player.playVideo();
            break;
        case 'pause':
            player.pauseVideo();
            break;
        case 'fast_forward':
            const currentTimeFF = player.getCurrentTime();
            player.seekTo(currentTimeFF + 10);
            break;
        case 'rewind':
            const currentTimeRW = player.getCurrentTime();
            player.seekTo(Math.max(0, currentTimeRW - 10));
            break;
        case 'volume_up':
            const currentVolumeUp = player.getVolume();
            player.setVolume(Math.min(100, currentVolumeUp + 10));
            break;
        case 'volume_down':
            const currentVolumeDown = player.getVolume();
            player.setVolume(Math.max(0, currentVolumeDown - 10));
            break;
    }
}

// Get feedback message for action
function getFeedbackMessage(action) {
    const messages = {
        'play': 'Play detected',
        'pause': 'Pause detected',
        'fast_forward': 'Fast Forward',
        'rewind': 'Rewind',
        'volume_up': 'Volume Up',
        'volume_down': 'Volume Down'
    };
    return messages[action] || 'Unknown action';
}

// Show feedback overlay
function showFeedback(message) {
    const feedbackElement = document.getElementById('gesture-feedback');
    feedbackElement.textContent = message;
    feedbackElement.classList.add('show');

    // Hide after 2 seconds
    setTimeout(() => {
        feedbackElement.classList.remove('show');
    }, 2000);
}

// Cleanup on page unload
window.addEventListener('beforeunload', () => {
    if (socket) {
        socket.emit('stop_stream');
        socket.disconnect();
    }
    if (webcamStream) {
        webcamStream.getTracks().forEach(track => track.stop());
    }
});
