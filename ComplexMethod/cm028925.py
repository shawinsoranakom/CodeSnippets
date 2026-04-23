def create_lower_mouth_mask(
    face: Face, frame: Frame
) -> (np.ndarray, np.ndarray, tuple, np.ndarray):
    mask = np.zeros(frame.shape[:2], dtype=np.uint8)
    mouth_cutout = None
    lower_lip_polygon = None # Initialize
    mouth_box = (0,0,0,0) # Initialize

    # Validate face and landmarks
    if face is None or not hasattr(face, 'landmark_2d_106'):
        # print("Warning: Invalid face object passed to create_lower_mouth_mask.")
        return mask, mouth_cutout, mouth_box, lower_lip_polygon

    landmarks = face.landmark_2d_106

    # Check landmark validity
    if landmarks is None or not isinstance(landmarks, np.ndarray) or landmarks.shape[0] < 106:
        # print("Warning: Invalid or insufficient landmarks for mouth mask.")
        return mask, mouth_cutout, mouth_box, lower_lip_polygon

    try: # Wrap main logic in try-except
        # Use outer mouth landmarks (52-71) to capture the full mouth area
        # This covers both upper and lower lips for proper mouth preservation
        lower_lip_order = list(range(52, 72))

        # Check if all indices are valid for the loaded landmarks (already partially done by < 106 check)
        if max(lower_lip_order) >= landmarks.shape[0]:
            # print(f"Warning: Landmark index {max(lower_lip_order)} out of bounds for shape {landmarks.shape[0]}.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

        lower_lip_landmarks = landmarks[lower_lip_order].astype(np.float32)

        # Filter out potential NaN or Inf values in landmarks
        if not np.all(np.isfinite(lower_lip_landmarks)):
            # print("Warning: Non-finite values detected in lower lip landmarks.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

        center = np.mean(lower_lip_landmarks, axis=0)
        if not np.all(np.isfinite(center)): # Check center calculation
            # print("Warning: Could not calculate valid center for mouth mask.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon


        mouth_mask_size = getattr(modules.globals, "mouth_mask_size", 0.0) # 0-100 slider
        # 0=tight lip outline, 50=covers mouth area, 100=mouth to chin
        expansion_factor = 1 + (mouth_mask_size / 100.0) * 2.5

        # Expand landmarks from center, with extra downward bias toward chin
        offsets = lower_lip_landmarks - center
        # Add extra downward expansion for points below center (toward chin)
        chin_bias = 1 + (mouth_mask_size / 100.0) * 1.5  # extra vertical stretch downward
        scale_y = np.where(offsets[:, 1] > 0, expansion_factor * chin_bias, expansion_factor)
        expanded_landmarks = lower_lip_landmarks.copy()
        expanded_landmarks[:, 0] = center[0] + offsets[:, 0] * expansion_factor
        expanded_landmarks[:, 1] = center[1] + offsets[:, 1] * scale_y

        # Ensure landmarks are finite after adjustments
        if not np.all(np.isfinite(expanded_landmarks)):
            # print("Warning: Non-finite values detected after expanding landmarks.")
            return mask, mouth_cutout, mouth_box, lower_lip_polygon

        expanded_landmarks = expanded_landmarks.astype(np.int32)

        min_x, min_y = np.min(expanded_landmarks, axis=0)
        max_x, max_y = np.max(expanded_landmarks, axis=0)

        # Add padding *after* initial min/max calculation
        padding_ratio = 0.1 # Percentage padding
        padding_x = int((max_x - min_x) * padding_ratio)
        padding_y = int((max_y - min_y) * padding_ratio) # Use y-range for y-padding

        # Apply padding and clamp to frame boundaries
        frame_h, frame_w = frame.shape[:2]
        min_x = max(0, min_x - padding_x)
        min_y = max(0, min_y - padding_y)
        max_x = min(frame_w, max_x + padding_x)
        max_y = min(frame_h, max_y + padding_y)


        if max_x > min_x and max_y > min_y:
            # Create the mask ROI
            mask_roi_h = max_y - min_y
            mask_roi_w = max_x - min_x
            mask_roi = np.zeros((mask_roi_h, mask_roi_w), dtype=np.uint8)

            # Shift polygon coordinates relative to the ROI's top-left corner
            polygon_relative_to_roi = expanded_landmarks - [min_x, min_y]

            # Draw polygon on the ROI mask
            cv2.fillPoly(mask_roi, [polygon_relative_to_roi], 255)

            # Apply Gaussian blur (GPU-accelerated when available)
            blur_k_size = getattr(modules.globals, "mask_blur_kernel", 15) # Default 15
            blur_k_size = max(1, blur_k_size // 2 * 2 + 1) # Ensure odd
            mask_roi = gpu_gaussian_blur(mask_roi, (blur_k_size, blur_k_size), 0)

            # Place the mask ROI in the full-sized mask
            mask[min_y:max_y, min_x:max_x] = mask_roi

            # Extract the masked area from the *original* frame
            mouth_cutout = frame[min_y:max_y, min_x:max_x].copy()

            lower_lip_polygon = expanded_landmarks # Return polygon in original frame coords
            mouth_box = (min_x, min_y, max_x, max_y) # Return the calculated box
        else:
            # print("Warning: Invalid mouth mask bounding box after padding/clamping.") # Optional debug
            pass

    except IndexError as idx_e:
        # print(f"Warning: Landmark index out of bounds during mouth mask creation: {idx_e}") # Optional debug
        pass
    except Exception as e:
        print(f"Error in create_lower_mouth_mask: {e}") # Print unexpected errors
        # import traceback
        # traceback.print_exc()
        pass

    # Return values, ensuring defaults if errors occurred
    return mask, mouth_cutout, mouth_box, lower_lip_polygon