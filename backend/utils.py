#used to show fps in the corner of the screen, but now it's just a utility function to get the current fps

import time

previous_time = 0

def get_fps():

    global previous_time

    current_time = time.time()

    fps = 1 / (current_time - previous_time)

    previous_time = current_time

    return int(fps)