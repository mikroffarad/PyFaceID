from camera import Camera, CameraConfig

def show_available_resolutions() -> None:
    """Displays supported resolutions"""
    print("\nAvailable resolutions:")
    resolutions = CameraConfig.get_supported_resolutions()

    # Display adaptive resolution first
    screen_width, screen_height = resolutions[0]
    print(f"0: Adaptive ({screen_width}x{screen_height} - Screen Resolution)")

    # Display other resolutions
    for i, (width, height) in enumerate(resolutions[1:], 1):
        name = CameraConfig.get_resolution_name(width, height)
        print(f"{i}: {width}x{height} ({name})")

def get_resolution_choice() -> int:
    """Gets user's resolution choice"""
    try:
        return int(input("\nSelect resolution number (-1 to keep current): "))
    except ValueError:
        return -1

def apply_resolution(camera: Camera, resolution_index: int) -> None:
    """Applies selected resolution to camera"""
    resolutions = CameraConfig.get_supported_resolutions()

    if 0 <= resolution_index < len(resolutions):
        new_width, new_height = resolutions[resolution_index]
        actual_width, actual_height = camera.set_resolution(new_width, new_height)

        if resolution_index == 0:
            print(f"\nSet adaptive resolution: {actual_width}x{actual_height}")
        else:
            name = CameraConfig.get_resolution_name(new_width, new_height)
            print(f"\nSet resolution: {actual_width}x{actual_height} ({name})")

        if (actual_width, actual_height) != (new_width, new_height):
            print("Note: Camera set the closest supported resolution")
    else:
        print("Keeping current resolution")
