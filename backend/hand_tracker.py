import cv2
import mediapipe as mp


class HandTracker:

    def __init__(
        self,
        max_hands=2,
        detection_confidence=0.5,
        tracking_confidence=0.5
    ):

        self.mp_hands = mp.solutions.hands
        self.mp_draw = mp.solutions.drawing_utils

        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=max_hands,
            min_detection_confidence=detection_confidence,
            min_tracking_confidence=tracking_confidence
        )

    def find_hands(self, frame, draw=True):

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        results = self.hands.process(rgb)

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                if draw:

                    self.mp_draw.draw_landmarks(
                        frame,
                        hand_landmarks,
                        self.mp_hands.HAND_CONNECTIONS
                    )

        return frame, results

    def get_hands(self, results, frame_width, frame_height):
        """
        Returns a list of hands (up to max_hands), each hand being a list
        of (landmark_id, pixel_x, pixel_y) tuples. Supports multi-hand use:
        hands[0] is treated as the "primary" pointer hand by main.py, any
        additional hands are used for auxiliary gestures only.
        """

        hands_list = []

        if results.multi_hand_landmarks:

            for hand_landmarks in results.multi_hand_landmarks:

                landmark_list = []

                for landmark_id, landmark in enumerate(hand_landmarks.landmark):
                    pixel_x = int(landmark.x * frame_width)
                    pixel_y = int(landmark.y * frame_height)
                    landmark_list.append((landmark_id, pixel_x, pixel_y))

                hands_list.append(landmark_list)

        return hands_list

    def get_landmarks(self, results, frame_width, frame_height):
        """
        Backwards-compatible helper: returns just the first detected hand's
        landmarks (or an empty list). Prefer get_hands() for multi-hand use.
        """
        hands = self.get_hands(results, frame_width, frame_height)
        return hands[0] if hands else []
