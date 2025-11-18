from flask import Flask, render_template, request, redirect, url_for
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import threading
import time
from modules.actions import ActionHandler
from modules.utils import extract_youtube_id

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables for video processing
cap = None
action_handler = ActionHandler()
processing_thread = None
is_processing = False

# Simple gesture detection without MediaPipe (fallback)
class SimpleGestureDetector:
    def __init__(self):
        self.prev_positions = {}
        self.gesture_cooldown = {}

    def detect_gesture(self, frame):
        # Convert to grayscale for motion detection
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        gray = cv2.GaussianBlur(gray, (21, 21), 0)

        if not hasattr(self, 'prev_gray'):
            self.prev_gray = gray
            return None

        # Calculate frame difference
        frame_delta = cv2.absdiff(self.prev_gray, gray)
        thresh = cv2.threshold(frame_delta, 25, 255, cv2.THRESH_BINARY)[1]
        thresh = cv2.dilate(thresh, None, iterations=2)

        # Find contours
        contours, _ = cv2.findContours(thresh.copy(), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        self.prev_gray = gray

        if contours:
            # Get largest contour
            largest_contour = max(contours, key=cv2.contourArea)
            if cv2.contourArea(largest_contour) > 500:  # Minimum area threshold
                x, y, w, h = cv2.boundingRect(largest_contour)
                center_x = x + w/2
                center_y = y + h/2

                # Simple gesture detection based on position and movement
                frame_center_x = frame.shape[1] / 2

                if center_x < frame_center_x - 50:
                    return "raise_left"
                elif center_x > frame_center_x + 50:
                    return "raise_right"

        return None

detector = SimpleGestureDetector()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/player', methods=['POST'])
def player():
    video_url = request.form.get('video_url')
    if not video_url:
        return redirect(url_for('index'))
    video_id = extract_youtube_id(video_url)
    if not video_id:
        return redirect(url_for('index'))
    return render_template('player.html', video_id=video_id)

@socketio.on('start_stream')
def start_stream():
    global cap, processing_thread, is_processing
    if cap is None:
        cap = cv2.VideoCapture(0)
    if not is_processing:
        is_processing = True
        processing_thread = threading.Thread(target=process_video_stream)
        processing_thread.start()

@socketio.on('stop_stream')
def stop_stream():
    global cap, is_processing
    is_processing = False
    if cap:
        cap.release()
        cap = None

def process_video_stream():
    global cap, is_processing
    while is_processing and cap and cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            continue

        # Process frame for gestures
        gesture = detector.detect_gesture(frame)

        # Handle action if gesture detected
        if gesture:
            action = action_handler.handle_gesture(gesture)
            if action:
                socketio.emit('gesture_action', {'action': action, 'gesture': gesture})

        # Send frame to frontend for display
        _, buffer = cv2.imencode('.jpg', frame)
        frame_data = base64.b64encode(buffer).decode('utf-8')
        socketio.emit('video_frame', {'frame': frame_data})

        time.sleep(0.1)  # Control frame rate

if __name__ == '__main__':
    socketio.run(app, debug=True, host='0.0.0.0', port=5000)
