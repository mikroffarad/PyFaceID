import cv2

def list_cameras():
    """Find all available cameras"""
    available_cameras = []
    index = 0

    # Check first 5 camera indexes
    while index < 5:
        cap = cv2.VideoCapture(index)
        if cap.isOpened():
            # Get camera resolution
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            available_cameras.append({
                'index': index,
                'resolution': f"{width}x{height}"
            })
            cap.release()
        index += 1
    return available_cameras

def show_camera_stream(camera_index):
    """Show video stream from selected camera"""
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Error: Can't open camera {camera_index}")
        return

    print("Press 'q' to quit")

    while True:
        # Read the frame
        ret, frame = cap.read()

        if not ret:
            print("Error: Can't get the frame")
            break

        # Show the frame
        cv2.imshow('Camera Feed', frame)

        # Check pressed key
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    # Free resources
    cap.release()
    cv2.destroyAllWindows()
