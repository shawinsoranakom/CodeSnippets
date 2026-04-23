def draw_mouth_mask_visualization(
    frame: Frame, face: Face, mouth_mask_data: tuple
) -> Frame:

    # Validate inputs
    if frame is None or face is None or mouth_mask_data is None or len(mouth_mask_data) != 4:
        return frame # Return original frame if inputs are invalid

    mask, mouth_cutout, box, lower_lip_polygon = mouth_mask_data
    (min_x, min_y, max_x, max_y) = box

    # Check if polygon is valid for drawing
    if lower_lip_polygon is None or not isinstance(lower_lip_polygon, np.ndarray) or len(lower_lip_polygon) < 3:
        return frame # Cannot draw without a valid polygon

    vis_frame = frame.copy()
    height, width = vis_frame.shape[:2]

    # Ensure box coordinates are valid integers within frame bounds
    try:
        min_x, min_y = max(0, int(min_x)), max(0, int(min_y))
        max_x, max_y = min(width, int(max_x)), min(height, int(max_y))
    except ValueError:
        # print("Warning: Invalid coordinates for mask visualization box.")
        return frame

    if max_x <= min_x or max_y <= min_y:
        return frame # Invalid box

    # Draw the lower lip polygon (green outline)
    try:
         # Ensure polygon points are within frame boundaries before drawing
         safe_polygon = lower_lip_polygon.copy()
         safe_polygon[:, 0] = np.clip(safe_polygon[:, 0], 0, width - 1)
         safe_polygon[:, 1] = np.clip(safe_polygon[:, 1], 0, height - 1)
         cv2.polylines(vis_frame, [safe_polygon.astype(np.int32)], isClosed=True, color=(0, 255, 0), thickness=2)
    except Exception as e:
        print(f"Error drawing polygon for visualization: {e}") # Optional debug
        pass

    # Draw bounding box (red rectangle)
    cv2.rectangle(vis_frame, (min_x, min_y), (max_x, max_y), (0, 0, 255), 2)

    # Optional: Add labels
    label_pos_y = min_y - 10 if min_y > 20 else max_y + 15 # Adjust position based on box location
    label_pos_x = min_x
    try:
        cv2.putText(vis_frame, "Mouth Mask", (label_pos_x, label_pos_y),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1, cv2.LINE_AA)
    except Exception as e:
        # print(f"Error drawing text for visualization: {e}") # Optional debug
        pass


    return vis_frame