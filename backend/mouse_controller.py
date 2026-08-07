import time
import pyautogui

class MouseController:

    def __init__(self, smoothening=3):

        pyautogui.FAILSAFE = False
        pyautogui.PAUSE = 0

        self.screen_width, self.screen_height = pyautogui.size()

        self.prev_x = 0
        self.prev_y = 0

        self.smoothening = smoothening

        # When False (Fist gesture), move()/click()/scroll()/etc. are
        # no-ops until an Open Palm gesture sets it back to True.
        self.active = True

        self.is_dragging = False

    def set_active(self, active):
        self.active = active
        # Releasing control mid-drag would leave the mouse button stuck down
        if not active and self.is_dragging:
            self.end_drag()

    def move(self, x, y, frame_width, frame_height, margin):

        if not self.active:
            return

        x = max(margin, min(frame_width - margin, x))
        y = max(margin, min(frame_height - margin, y))

        screen_x = (x - margin) * self.screen_width / (frame_width - 2 * margin)
        screen_y = (y - margin) * self.screen_height / (frame_height - 2 * margin)

        current_x = self.prev_x + (screen_x - self.prev_x) / self.smoothening
        current_y = self.prev_y + (screen_y - self.prev_y) / self.smoothening

        pyautogui.moveTo(current_x, current_y)

        self.prev_x = current_x
        self.prev_y = current_y

    def click(self):
        """Left click - used for a short Pinch (release before drag threshold)."""
        if not self.active:
            return

        time.sleep(0.02)
        pyautogui.click()
        time.sleep(0.02)

    def right_click(self):
        """Right click - used for the thumb+middle-finger 'Right Pinch'."""
        if not self.active:
            return

        time.sleep(0.02)
        pyautogui.rightClick()
        time.sleep(0.02)

    def scroll(self, amount):
        """Positive amount scrolls up, negative scrolls down."""
        if not self.active:
            return
        pyautogui.scroll(int(amount))

    def start_drag(self):
        """Called once when a Pinch is held past the drag threshold."""
        if not self.active or self.is_dragging:
            return
        pyautogui.mouseDown()
        self.is_dragging = True

    def end_drag(self):
        """Called once when a held Pinch is released."""
        if not self.is_dragging:
            return
        pyautogui.mouseUp()
        self.is_dragging = False
