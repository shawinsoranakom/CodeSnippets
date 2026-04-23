def apply_post_processing(current_frame: Frame, swapped_face_bboxes: List[np.ndarray]) -> Frame:
    """Applies sharpening and interpolation with Apple Silicon optimizations."""
    global PREVIOUS_FRAME_RESULT

    sharpness_value = getattr(modules.globals, "sharpness", 0.0)
    enable_interpolation = getattr(modules.globals, "enable_interpolation", False)

    # Skip copy when no post-processing is active
    if sharpness_value <= 0.0 and not enable_interpolation:
        PREVIOUS_FRAME_RESULT = None
        return current_frame

    processed_frame = current_frame.copy()

    # 1. Apply Sharpening (if enabled) with optimized kernel for Apple Silicon
    sharpness_value = getattr(modules.globals, "sharpness", 0.0)
    if sharpness_value > 0.0 and swapped_face_bboxes:
        height, width = processed_frame.shape[:2]
        for bbox in swapped_face_bboxes:
            # Ensure bbox is iterable and has 4 elements
            if not hasattr(bbox, '__iter__') or len(bbox) != 4:
                # print(f"Warning: Invalid bbox format for sharpening: {bbox}") # Debug
                continue
            x1, y1, x2, y2 = bbox
            # Ensure coordinates are integers and within bounds
            try:
                 x1, y1 = max(0, int(x1)), max(0, int(y1))
                 x2, y2 = min(width, int(x2)), min(height, int(y2))
            except ValueError:
                # print(f"Warning: Could not convert bbox coordinates to int: {bbox}") # Debug
                continue


            if x2 <= x1 or y2 <= y1:
                continue

            face_region = processed_frame[y1:y2, x1:x2]
            if face_region.size == 0: continue

            # Apply sharpening (GPU-accelerated when CUDA OpenCV is available)
            try:
                sigma = 2 if IS_APPLE_SILICON else 3
                sharpened_region = gpu_sharpen(face_region, strength=sharpness_value, sigma=sigma)
                processed_frame[y1:y2, x1:x2] = sharpened_region
            except cv2.error:
                pass


    # 2. Apply Interpolation (if enabled)
    enable_interpolation = getattr(modules.globals, "enable_interpolation", False)
    interpolation_weight = getattr(modules.globals, "interpolation_weight", 0.2)

    final_frame = processed_frame # Start with the current (potentially sharpened) frame

    if enable_interpolation and 0 < interpolation_weight < 1:
        if PREVIOUS_FRAME_RESULT is not None and PREVIOUS_FRAME_RESULT.shape == processed_frame.shape and PREVIOUS_FRAME_RESULT.dtype == processed_frame.dtype:
            # Perform interpolation
            try:
                 final_frame = gpu_add_weighted(
                    PREVIOUS_FRAME_RESULT, 1.0 - interpolation_weight,
                    processed_frame, interpolation_weight,
                    0
                 )
                 # Ensure final frame is uint8
                 final_frame = np.clip(final_frame, 0, 255).astype(np.uint8)
            except cv2.error as interp_e:
                 # print(f"Warning: OpenCV error during interpolation: {interp_e}") # Debug
                 final_frame = processed_frame # Use current frame if interpolation fails
                 PREVIOUS_FRAME_RESULT = None # Reset state if error occurs

            # Update the state for the next frame *with the interpolated result*
            PREVIOUS_FRAME_RESULT = final_frame.copy()
        else:
            # If previous frame invalid or doesn't match, use current frame and update state
            if PREVIOUS_FRAME_RESULT is not None and PREVIOUS_FRAME_RESULT.shape != processed_frame.shape:
                # print("Info: Frame shape changed, resetting interpolation state.") # Debug
                pass
            PREVIOUS_FRAME_RESULT = processed_frame.copy()
    else:
         # Interpolation is off or weight is invalid — no need to cache
         PREVIOUS_FRAME_RESULT = None


    return final_frame