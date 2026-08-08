import os
import sys
import threading
import time
import cv2

if getattr(sys, "frozen", False):
    base_dir = sys._MEIPASS
    backend_path = os.path.join(base_dir, "backend")
else:
    base_dir = os.path.dirname(__file__)
    backend_path = os.path.join(base_dir, "..", "backend")

sys.path.insert(0, os.path.abspath(backend_path))

import config
from hand_tracker import HandTracker
from gesture_detector import GestureDetector
from ml_gesture_classifier import MLGestureClassifier
from mouse_controller import MouseController
from face_analyzer import FaceAnalyzer
from voice_feedback import VoiceFeedback
from session_logger import SessionLogger
import system_control

FREEZE_GESTURES = {"Fist", "Peace", "Thumbs Up", "Thumbs Down", "Right Pinch", "Scroll"}
SHARED_ACTION_GESTURES = {"Fist", "Open Palm", "Peace", "Thumbs Up", "Thumbs Down"}

class AssistantWorker:
    """Owns the camera + detection loop on a background thread. All
    getters/setters are thread-safe so the Tkinter GUI can poll freely."""

    def __init__(self):
        self._lock = threading.Lock()
        self._latest_frame = None  # RGB numpy array, ready for the GUI
        self._latest_state = {
            "gesture": "None", "confidence": 0.0, "hand_count": 0,
            "mouse_active": True, "face_count": 0, "emotion": "-",
            "emotion_confidence": 0.0, "fps": 0, "wink_text": None,
            "head_gesture_text": None, "action_fired": False, "running": False,
        }
        self._stop_event = threading.Event()
        self._pause_mouse_request = None  # None / True / False, consumed each frame
        self._thread = None

        self.volume = system_control.VolumeControl()
        self.brightness = system_control.BrightnessControl()
        self.voice = VoiceFeedback(config.VOICE_FEEDBACK_ENABLED)
        self.logger = SessionLogger(config.SESSION_LOGGING_ENABLED, config.LOG_DIR)

    # ------------------------------------------------------------------
    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=2)
        self.logger.close()

    def request_mouse_active(self, active):
        self._pause_mouse_request = active

    def get_frame(self):
        with self._lock:
            return self._latest_frame

    def get_state(self):
        with self._lock:
            return dict(self._latest_state)

    # ------------------------------------------------------------------
    def _run(self):
        camera = cv2.VideoCapture(config.CAMERA_INDEX)
        camera.set(cv2.CAP_PROP_FRAME_WIDTH, config.FRAME_WIDTH)
        camera.set(cv2.CAP_PROP_FRAME_HEIGHT, config.FRAME_HEIGHT)

        tracker = HandTracker(max_hands=config.MAX_HANDS)
        mouse = MouseController(config.SMOOTHENING)
        rule_gestures = GestureDetector()
        ml_gestures = MLGestureClassifier()
        face_analyzer = FaceAnalyzer()

        mouse_active = True
        last_gesture = [None, None]
        last_action_time = [{}, {}]
        pinch_start_time = None
        prev_scroll_y = None
        last_hand_seen_time = time.time()
        action_fired_until = 0.0
        prev_time = 0

        def dispatch_shared_action(name):
            nonlocal mouse_active
            if name == "Thumbs Up":
                self.volume.volume_up()
                self.logger.log("volume_up")
            elif name == "Thumbs Down":
                self.volume.volume_down()
                self.logger.log("volume_down")
            elif name == "Fist":
                mouse_active = False
                mouse.set_active(False)
                self.voice.speak("Mouse paused")
                self.logger.log("mouse_paused")
            elif name == "Open Palm":
                mouse_active = True
                mouse.set_active(True)
                self.voice.speak("Mouse resumed")
                self.logger.log("mouse_resumed")

        with self._lock:
            self._latest_state["running"] = True

        while not self._stop_event.is_set():

            if self._pause_mouse_request is not None:
                mouse_active = self._pause_mouse_request
                mouse.set_active(mouse_active)
                self._pause_mouse_request = None

            success, frame = camera.read()
            if not success:
                time.sleep(0.05)
                continue

            frame = cv2.flip(frame, 1)
            frame, results = tracker.find_hands(frame)
            h, w, _ = frame.shape
            margin = config.FRAME_MARGIN
            hands = tracker.get_hands(results, w, h)

            cv2.rectangle(frame, (margin, margin), (w - margin, h - margin), config.GREEN, 2)

            gesture_name_display = "None"
            confidence_display = 0.0
            action_fired = False

            if hands:
                last_hand_seen_time = time.time()

            idle = (
                config.IDLE_TIMEOUT > 0
                and mouse_active
                and (time.time() - last_hand_seen_time) > config.IDLE_TIMEOUT
            )
            if idle:
                mouse_active = False
                mouse.set_active(False)
                self.logger.log("idle_auto_pause")

            for slot in range(2):
                if slot >= len(hands):
                    last_gesture[slot] = None
                    if slot == 0:
                        pinch_start_time = None
                        prev_scroll_y = None
                    continue

                landmarks = hands[slot]

                if ml_gestures.is_ready():
                    gesture_name, confidence = ml_gestures.predict(landmarks)
                else:
                    gesture_name, confidence = rule_gestures.classify(landmarks)

                if slot == 0:
                    gesture_name_display, confidence_display = gesture_name, confidence
                    index_tip = landmarks[10]

                    if mouse_active and gesture_name not in FREEZE_GESTURES:
                        mouse.move(index_tip[1], index_tip[2], w, h, margin)

                    if gesture_name == "Pinch":
                        if pinch_start_time is None:
                            pinch_start_time = time.time()
                        held = time.time() - pinch_start_time
                        if held > config.DRAG_HOLD_TIME and not mouse.is_dragging:
                            mouse.start_drag()
                            self.voice.speak("Drag")
                            self.logger.log("drag_start")
                        cv2.putText(frame, "DRAG" if mouse.is_dragging else "CLICK", (20, 80),
                                    cv2.FONT_HERSHEY_SIMPLEX, 0.8, config.RED, 2)
                    else:
                        if pinch_start_time is not None:
                            held = time.time() - pinch_start_time
                            if mouse.is_dragging:
                                mouse.end_drag()
                                self.logger.log("drag_end")
                            elif held <= config.DRAG_HOLD_TIME:
                                mouse.click()
                                action_fired = True
                                self.voice.speak("Click")
                                self.logger.log("click")
                            pinch_start_time = None

                    if gesture_name == "Right Pinch" and last_gesture[0] != "Right Pinch":
                        mouse.right_click()
                        action_fired = True
                        self.voice.speak("Right click")
                        self.logger.log("right_click")

                    if gesture_name == "Scroll":
                        wrist_y = landmarks[0][2]
                        if prev_scroll_y is not None:
                            delta = prev_scroll_y - wrist_y
                            if abs(delta) > config.SCROLL_DEAD_ZONE:
                                mouse.scroll(delta * config.SCROLL_SPEED / 10)
                        prev_scroll_y = wrist_y
                    else:
                        prev_scroll_y = None

                if gesture_name in SHARED_ACTION_GESTURES:
                    if gesture_name in config.HOLD_REPEAT_GESTURES:
                        now = time.time()
                        if now - last_action_time[slot].get(gesture_name, 0) > config.ACTION_COOLDOWN:
                            dispatch_shared_action(gesture_name)
                            last_action_time[slot][gesture_name] = now
                            action_fired = True
                    else:
                        if gesture_name != last_gesture[slot]:
                            dispatch_shared_action(gesture_name)
                            action_fired = True

                last_gesture[slot] = gesture_name

            if action_fired:
                action_fired_until = time.time() + 0.3

            frame, faces = face_analyzer.analyze(frame)
            face_count = len(faces)
            emotion = faces[0]["emotion"] if faces else "-"
            emotion_conf = faces[0]["confidence"] if faces else 0.0

            wink_text = None
            head_gesture_text = None

            if faces:
                wink_event = faces[0]["wink_event"]
                if wink_event == "Left":
                    muted = self.volume.toggle_mute()
                    wink_text = "Wink: Mute toggled"
                    self.voice.speak("Muted" if muted else "Unmuted")
                    self.logger.log("wink_left_mute")
                elif wink_event == "Right":
                    system_control.next_track()
                    wink_text = "Wink: Next track"
                    self.voice.speak("Next track")
                    self.logger.log("wink_right_next_track")

                if faces[0]["nod_event"]:
                    system_control.play_pause()
                    head_gesture_text = "Nod: Play/Pause"
                    self.voice.speak("Play pause")
                    self.logger.log("nod_play_pause")
                elif faces[0]["shake_event"]:
                    system_control.previous_track()
                    head_gesture_text = "Shake: Previous track"
                    self.voice.speak("Previous track")
                    self.logger.log("shake_previous_track")

            current_time = time.time()
            fps = 1 / (current_time - prev_time) if prev_time != 0 else 0
            prev_time = current_time

            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

            with self._lock:
                self._latest_frame = rgb_frame
                self._latest_state.update({
                    "gesture": gesture_name_display,
                    "confidence": confidence_display,
                    "hand_count": len(hands),
                    "mouse_active": mouse_active,
                    "face_count": face_count,
                    "emotion": emotion,
                    "emotion_confidence": emotion_conf,
                    "fps": int(fps),
                    "wink_text": wink_text,
                    "head_gesture_text": head_gesture_text,
                    "action_fired": time.time() < action_fired_until,
                    "running": True,
                })

        camera.release()
        with self._lock:
            self._latest_state["running"] = False
