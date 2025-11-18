import time

class ActionHandler:
    def __init__(self, cooldown_time=2.0):
        """
        Initialize action handler with cooldown system
        cooldown_time: seconds to wait before allowing same gesture again
        """
        self.cooldown_time = cooldown_time
        self.last_actions = {}

    def handle_gesture(self, gesture):
        """
        Convert gesture to action, respecting cooldown
        Returns action string or None if on cooldown
        """
        current_time = time.time()

        # Check cooldown
        if gesture in self.last_actions:
            if current_time - self.last_actions[gesture] < self.cooldown_time:
                return None  # Still on cooldown

        # Update last action time
        self.last_actions[gesture] = current_time

        # Map gestures to actions
        gesture_to_action = {
            "raise_right": "play",
            "raise_left": "pause",
            "swipe_right": "fast_forward",
            "swipe_left": "rewind",
            "push_forward": "volume_up",
            "pull_backward": "volume_down"
        }

        return gesture_to_action.get(gesture)

    def get_feedback_message(self, action):
        """
        Get user-friendly feedback message for action
        """
        action_messages = {
            "play": "Play detected",
            "pause": "Pause detected",
            "fast_forward": "Fast Forward",
            "rewind": "Rewind",
            "volume_up": "Volume Up",
            "volume_down": "Volume Down"
        }

        return action_messages.get(action, "Unknown action")
