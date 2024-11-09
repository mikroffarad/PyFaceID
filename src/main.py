from typing import List, Dict, Optional
from camera import Camera, find_available_cameras
from resolution_manager import *
from camera_stream import display_camera_stream

def select_camera(cameras: List[Dict[str, any]]) -> Optional[int]:
    """
    Prompts user to select a camera
    Returns:
        Optional[int]: Camera index if selected, None if user wants to exit
    """
    print("\nAvailable cameras:")
    for camera in cameras:
        print(f"Camera {camera['index']}: {camera['resolution']}")
    print("\nPress 'q' to exit or select camera number")

    while True:
        try:
            selection = input("\nYour choice: ").strip().lower()
            if selection == 'q':
                return None

            selected = int(selection)
            if any(camera['index'] == selected for camera in cameras):
                return selected
            print("Incorrect camera number. Try again.")
        except ValueError:
            print("Please input a number or 'q' to exit")


def setup_camera_stream(camera_index: int) -> bool:
    """Sets up and starts camera stream with user-selected settings"""
    camera = Camera(camera_index)

    if not camera.open():
        print(f"Error: Unable to open camera with index {camera_index}")
        return False

    # Show current resolution
    width, height = camera.get_resolution()
    print(f"\nCurrent resolution: {width}x{height}")

    # Handle resolution selection
    show_available_resolutions()
    resolution_choice = get_resolution_choice()
    apply_resolution(camera, resolution_choice)

    print("\nPress 'q' to return to camera selection")

    # Start streaming
    result = display_camera_stream(camera)
    camera.close()
    return result

def main():
    """Main application loop"""
    while True:
        cameras = find_available_cameras()

        if not cameras:
            print("No cameras found")
            return

        selected_camera = select_camera(cameras)

        if selected_camera is None:
            print("Exiting program...")
            break

        if not setup_camera_stream(selected_camera):
            print("Error occurred with camera stream")
            break

if __name__ == "__main__":
    main()
