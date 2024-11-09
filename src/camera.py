import cv2
from typing import List, Tuple, Dict, Optional
import tkinter as tk

class CameraConfig:
    """Constants and configuration for camera handling"""
    MAX_CAMERAS_TO_CHECK = 5

    @staticmethod
    def get_supported_resolutions() -> List[Tuple[int, int]]:
        """Returns list of supported resolutions including adaptive screen resolution"""
        # Get screen resolution
        root = tk.Tk()
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        root.destroy()

        return [
            (screen_width, screen_height),  # Adaptive (Screen Resolution)
            (640, 480),    # VGA
            (800, 600),    # SVGA
            (1024, 768),   # XGA
            (1280, 720),   # HD
            (1920, 1080),  # Full HD
            (2560, 1440),  # 2K
            (3840, 2160)   # 4K
        ]

    @staticmethod
    def get_resolution_name(width: int, height: int) -> str:
        """Returns human-readable name for resolution"""
        resolution_names = {
            (640, 480): "VGA",
            (800, 600): "SVGA",
            (1024, 768): "XGA",
            (1280, 720): "HD",
            (1920, 1080): "Full HD",
            (2560, 1440): "2K",
            (3840, 2160): "4K"
        }
        return resolution_names.get((width, height), f"{width}x{height}")

class Camera:
    def __init__(self, index: int):
        self.index = index
        self.cap = None

    def open(self) -> bool:
        """Opens the camera connection"""
        self.cap = cv2.VideoCapture(self.index)
        return self.cap.isOpened()

    def close(self) -> None:
        """Closes the camera connection"""
        if self.cap is not None:
            self.cap.release()
        cv2.destroyAllWindows()

    def get_resolution(self) -> Tuple[int, int]:
        """Returns current camera resolution"""
        if self.cap is None:
            return (0, 0)
        width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        return (width, height)

    def set_resolution(self, width: int, height: int) -> Tuple[int, int]:
        """Sets camera resolution and returns actual values"""
        if self.cap is None:
            return (0, 0)
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)
        return self.get_resolution()

    def read_frame(self) -> Tuple[bool, Optional[object]]:
        """Reads a single frame from the camera"""
        if self.cap is None:
            return False, None
        return self.cap.read()

def find_available_cameras() -> List[Dict[str, any]]:
    """Detects and returns a list of available cameras with their properties"""
    available_cameras = []

    for index in range(CameraConfig.MAX_CAMERAS_TO_CHECK):
        camera = Camera(index)
        if camera.open():
            width, height = camera.get_resolution()
            available_cameras.append({
                'index': index,
                'resolution': f"{width}x{height}"
            })
            camera.close()

    return available_cameras
