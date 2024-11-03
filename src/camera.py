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

def get_supported_resolutions():
    """Returns a list of typical resolutions"""
    return [
        (640, 480),    # VGA
        (800, 600),    # SVGA
        (1024, 768),   # XGA
        (1280, 720),   # HD
        (1920, 1080),  # Full HD
        (2560, 1440),  # 2K
        (3840, 2160)   # 4K
    ]

def set_camera_resolution(cap, width, height):
    """Sets camera resolution and returns actual values"""
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, width)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, height)

    # Check if the requested resolution was actually set
    actual_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    actual_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    return actual_width, actual_height

def show_camera_stream(camera_index):
    """Shows video stream from the selected camera"""
    cap = cv2.VideoCapture(camera_index)

    if not cap.isOpened():
        print(f"Error: Unable to open camera with index {camera_index}")
        return

    # Get current resolution
    current_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    current_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    print(f"\nCurrent resolution: {current_width}x{current_height}")

    # Show available resolutions
    resolutions = get_supported_resolutions()
    print("\nAvailable resolutions:")
    for i, (width, height) in enumerate(resolutions):
        print(f"{i}: {width}x{height}")

    # Ask user for desired resolution
    try:
        choice = int(input("\nSelect resolution number (-1 to keep current): "))
        if 0 <= choice < len(resolutions):
            new_width, new_height = resolutions[choice]
            actual_width, actual_height = set_camera_resolution(cap, new_width, new_height)
            print(f"\nSet resolution: {actual_width}x{actual_height}")
            if actual_width != new_width or actual_height != new_height:
                print("Note: Camera set the closest supported resolution")
    except ValueError:
        print("Keeping current resolution")

    print("\nPress 'q' to exit")

    while True:
        ret, frame = cap.read()

        if not ret:
            print("Error: Unable to get frame")
            break

        cv2.imshow('Camera Feed', frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()
