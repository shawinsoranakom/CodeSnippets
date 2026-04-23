def click_event(event: int, x: int, y: int, flags: int, param) -> None:
    """Handle mouse click events to select an object for focused tracking.

    Args:
        event (int): OpenCV mouse event type.
        x (int): X-coordinate of the mouse event.
        y (int): Y-coordinate of the mouse event.
        flags (int): Any relevant flags passed by OpenCV.
        param (Any): Additional parameters (not used).
    """
    global selected_object_id, latest_detections
    if event == cv2.EVENT_LBUTTONDOWN:
        if not latest_detections:
            return
        min_area = float("inf")
        best_match = None
        for track in latest_detections:
            if len(track) < 6:
                continue
            x1, y1, x2, y2 = map(int, track[:4])
            if x1 <= x <= x2 and y1 <= y <= y2:
                area = max(0, x2 - x1) * max(0, y2 - y1)
                if area < min_area:
                    track_id = int(track[4]) if len(track) >= 7 else -1
                    class_id = int(track[6]) if len(track) >= 7 else int(track[5])
                    min_area = area
                    best_match = (track_id, classes.get(class_id, str(class_id)))
        if best_match:
            selected_object_id, label = best_match
            LOGGER.info(f"Tracking started: {label} (ID {selected_object_id})")