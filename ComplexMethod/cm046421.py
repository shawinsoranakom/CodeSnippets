def mouse_callback(event: int, x: int, y: int, flags: int, param: Any) -> None:
    """Handle mouse events for region manipulation in the video frame.

    This function enables interactive region selection and dragging functionality for counting regions. It responds to
    mouse button down, move, and up events to allow users to select and reposition counting regions in real-time.

    Args:
        event (int): The mouse event type (e.g., cv2.EVENT_LBUTTONDOWN, cv2.EVENT_MOUSEMOVE).
        x (int): The x-coordinate of the mouse pointer.
        y (int): The y-coordinate of the mouse pointer.
        flags (int): Additional flags passed by OpenCV.
        param (Any): Additional parameters passed to the callback.

    Examples:
        Set up mouse callback for interactive region manipulation
        >>> cv2.setMouseCallback("window_name", mouse_callback)
    """
    global current_region

    # Mouse left button down event
    if event == cv2.EVENT_LBUTTONDOWN:
        for region in counting_regions:
            if region["polygon"].contains(Point((x, y))):
                current_region = region
                current_region["dragging"] = True
                current_region["offset_x"] = x
                current_region["offset_y"] = y

    # Mouse move event
    elif event == cv2.EVENT_MOUSEMOVE:
        if current_region is not None and current_region["dragging"]:
            dx = x - current_region["offset_x"]
            dy = y - current_region["offset_y"]
            current_region["polygon"] = Polygon(
                [(p[0] + dx, p[1] + dy) for p in current_region["polygon"].exterior.coords]
            )
            current_region["offset_x"] = x
            current_region["offset_y"] = y

    # Mouse left button up event
    elif event == cv2.EVENT_LBUTTONUP:
        if current_region is not None and current_region["dragging"]:
            current_region["dragging"] = False