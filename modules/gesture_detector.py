import cv2
import mediapipe as mp
import numpy as np

class GestureDetector:
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=0.7,
            min_tracking_confidence=0.5
        )
        self.mp_draw = mp.solutions.drawing_utils

        # Gesture tracking variables
        self.prev_hand_positions = {}
        self.gesture_cooldown = {}

    def detect_gesture(self, frame):
        """
        Detect hand gestures from video frame
        Returns gesture type or None
        """
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.hands.process(rgb_frame)

        if not results.multi_hand_landmarks:
            return None

        gestures = []

        for hand_idx, hand_landmarks in enumerate(results.multi_hand_landmarks):
            gesture = self._analyze_hand_gesture(hand_landmarks, hand_idx)
            if gesture:
                gestures.append(gesture)

        # Return the first detected gesture
        return gestures[0] if gestures else None

    def _analyze_hand_gesture(self, hand_landmarks, hand_idx):
        """
        Analyze individual hand landmarks to detect specific gestures
        """
        # Extract key landmark positions
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        thumb_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP]
        index_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP]
        middle_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP]
        ring_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP]
        pinky_tip = hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]

        # Calculate hand center and orientation
        hand_center_x = np.mean([lm.x for lm in hand_landmarks.landmark])
        hand_center_y = np.mean([lm.y for lm in hand_landmarks.landmark])

        # Check for raised hand gestures
        if self._is_hand_raised(hand_landmarks):
            if hand_center_x < 0.5:  # Left side of frame
                return "raise_left"
            else:  # Right side of frame
                return "raise_right"

        # Check for swipe gestures
        swipe_gesture = self._detect_swipe(hand_landmarks, hand_idx)
        if swipe_gesture:
            return swipe_gesture

        # Check for push/pull gestures (depth-based)
        depth_gesture = self._detect_depth_gesture(hand_landmarks, hand_idx)
        if depth_gesture:
            return depth_gesture

        return None

    def _is_hand_raised(self, hand_landmarks):
        """
        Check if hand is raised (all fingers extended upward)
        """
        # Simple check: if wrist is below fingertips on y-axis
        wrist = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]
        fingertips = [
            hand_landmarks.landmark[self.mp_hands.HandLandmark.THUMB_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.INDEX_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.MIDDLE_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.RING_FINGER_TIP],
            hand_landmarks.landmark[self.mp_hands.HandLandmark.PINKY_TIP]
        ]

        # Check if wrist is below all fingertips
        return all(wrist.y > tip.y for tip in fingertips)

    def _detect_swipe(self, hand_landmarks, hand_idx):
        """
        Detect horizontal swipe gestures
        """
        current_pos = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST]

        if hand_idx not in self.prev_hand_positions:
            self.prev_hand_positions[hand_idx] = current_pos
            return None

        prev_pos = self.prev_hand_positions[hand_idx]
        delta_x = current_pos.x - prev_pos.x
        delta_y = current_pos.y - prev_pos.y

        # Update previous position
        self.prev_hand_positions[hand_idx] = current_pos

        # Check for significant horizontal movement
        if abs(delta_x) > 0.1 and abs(delta_y) < 0.05:  # Horizontal swipe
            if delta_x > 0:
                return "swipe_right"
            else:
                return "swipe_left"

        return None

    def _detect_depth_gesture(self, hand_landmarks, hand_idx):
        """
        Detect push/pull gestures based on hand depth (z-coordinate)
        """
        current_z = hand_landmarks.landmark[self.mp_hands.HandLandmark.WRIST].z

        if hand_idx not in self.prev_hand_positions:
            self.prev_hand_positions[hand_idx] = type('obj', (object,), {'z': current_z})
            return None

        prev_z = self.prev_hand_positions[hand_idx].z
        delta_z = current_z - prev_z

        # Update z position
        self.prev_hand_positions[hand_idx].z = current_z

        # Check for significant depth change
        if abs(delta_z) > 0.05:
            if delta_z < 0:  # Moving toward camera
                return "push_forward"
            else:  # Moving away from camera
                return "pull_backward"

        return None

    def draw_landmarks(self, frame, hand_landmarks):
        """
        Draw hand landmarks on frame for visualization
        """
        self.mp_draw.draw_landmarks(frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
