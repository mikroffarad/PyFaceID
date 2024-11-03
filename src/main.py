from camera import list_cameras, show_camera_stream

def main():
    # Find available cameras
    cameras = list_cameras()

    if not cameras:
        print("Cameras not found")
        return

    # Print a list of available cameras
    print("\nAvailable cameras:")
    for camera in cameras:
        print(f"Camera {camera['index']}: {camera['resolution']}")

    # Ask user
    while True:
        try:
            selected = int(input("\nSelect a camera number: "))
            if any(camera['index'] == selected for camera in cameras):
                break
            print("Incorrect camera number. Try again.")
        except ValueError:
            print("Please, input a number")

    # Show a video from selected camera
    show_camera_stream(selected)

if __name__ == "__main__":
    main()
