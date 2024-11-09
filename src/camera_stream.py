import cv2
from camera import Camera
import tkinter as tk

def display_camera_stream(camera: Camera) -> bool:
    """Displays video stream from the camera until user exits"""
    # Create named window
    window_name = 'Camera Feed'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)

    # Get screen resolution
    screen = tk.Tk()
    screen_width = screen.winfo_screenwidth()
    screen_height = screen.winfo_screenheight()
    screen.destroy()

    # Set the size of the window a little smaller than the size of the screen,
    # to take into account the system panels
    cv2.resizeWindow(window_name, screen_width - 100, screen_height - 100)

    while True:
        ret, frame = camera.read_frame()
        if not ret:
            print("Error: Unable to get frame")
            return False

        cv2.imshow(window_name, frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            return True
