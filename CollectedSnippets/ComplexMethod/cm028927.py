def apply_mouth_area(
    frame: np.ndarray,
    mouth_cutout: np.ndarray,
    mouth_box: tuple,
    face_mask: np.ndarray, # Full face mask (for blending edges)
    mouth_polygon: np.ndarray, # Specific polygon for the mouth area itself
) -> np.ndarray:

    # Basic validation
    if (frame is None or mouth_cutout is None or mouth_box is None or
        face_mask is None or mouth_polygon is None):
        # print("Warning: Invalid input (None value) to apply_mouth_area") # Optional debug
        return frame
    if (mouth_cutout.size == 0 or face_mask.size == 0 or len(mouth_polygon) < 3):
        # print("Warning: Invalid input (empty array/polygon) to apply_mouth_area") # Optional debug
        return frame

    try: # Wrap main logic in try-except
        min_x, min_y, max_x, max_y = map(int, mouth_box) # Ensure integer coords
        box_width = max_x - min_x
        box_height = max_y - min_y

        # Check box validity
        if box_width <= 0 or box_height <= 0:
            # print("Warning: Invalid mouth box dimensions in apply_mouth_area.")
            return frame

        # Define the Region of Interest (ROI) on the target frame (swapped frame)
        frame_h, frame_w = frame.shape[:2]
        # Clamp coordinates strictly within frame boundaries
        min_y, max_y = max(0, min_y), min(frame_h, max_y)
        min_x, max_x = max(0, min_x), min(frame_w, max_x)

        # Recalculate box dimensions based on clamped coords
        box_width = max_x - min_x
        box_height = max_y - min_y
        if box_width <= 0 or box_height <= 0:
            # print("Warning: ROI became invalid after clamping in apply_mouth_area.")
            return frame # ROI is invalid

        roi = frame[min_y:max_y, min_x:max_x]

        # Ensure ROI extraction was successful
        if roi.size == 0:
            # print("Warning: Extracted ROI is empty in apply_mouth_area.")
            return frame

        # Resize mouth cutout from original frame to fit the ROI size
        resized_mouth_cutout = None
        if roi.shape[:2] != mouth_cutout.shape[:2]:
             # Check if mouth_cutout has valid dimensions before resizing
             if mouth_cutout.shape[0] > 0 and mouth_cutout.shape[1] > 0:
                  resized_mouth_cutout = gpu_resize(mouth_cutout, (box_width, box_height), interpolation=cv2.INTER_LINEAR)
             else:
                 # print("Warning: mouth_cutout has invalid dimensions, cannot resize.")
                 return frame # Cannot proceed without valid cutout
        else:
             resized_mouth_cutout = mouth_cutout

        # If resize failed or original was invalid
        if resized_mouth_cutout is None or resized_mouth_cutout.size == 0:
            # print("Warning: Mouth cutout is invalid after resize attempt.")
            return frame

        # --- Mask Creation ---
        # Create a mask based on the mouth_polygon, relative to the ROI
        polygon_mask_roi = np.zeros(roi.shape[:2], dtype=np.uint8)
        adjusted_polygon = mouth_polygon - [min_x, min_y]
        cv2.fillPoly(polygon_mask_roi, [adjusted_polygon.astype(np.int32)], 255)

        # Feather the edges with Gaussian blur for smooth blending
        feather_amount = max(1, min(30, min(box_width, box_height) // 8))
        kernel_size = 2 * feather_amount + 1
        feathered_mask = cv2.GaussianBlur(polygon_mask_roi.astype(np.float32), (kernel_size, kernel_size), 0)

        # Normalize to [0.0, 1.0]
        max_val = feathered_mask.max()
        if max_val > 1e-6:
            feathered_mask = feathered_mask / max_val
        else:
            feathered_mask.fill(0.0)

        # --- Blending: paste original mouth onto swapped face ---
        if len(frame.shape) == 3 and frame.shape[2] == 3:
            mask_3ch = feathered_mask[:, :, np.newaxis].astype(np.float32)
            inv_mask = 1.0 - mask_3ch

            # Blend: (original_mouth * mask) + (swapped_face * (1 - mask))
            blended_roi = (resized_mouth_cutout.astype(np.float32) * mask_3ch +
                           roi.astype(np.float32) * inv_mask)

            frame[min_y:max_y, min_x:max_x] = np.clip(blended_roi, 0, 255).astype(np.uint8)

    except Exception as e:
        print(f"Error applying mouth area: {e}") # Optional debug
        # import traceback
        # traceback.print_exc()
        pass # Don't crash, just return the frame as is

    return frame