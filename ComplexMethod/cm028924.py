def process_image(source_path: str, target_path: str, output_path: str) -> None:
    """Processes a single target image."""
    # --- Reset interpolation state for single image processing ---
    global PREVIOUS_FRAME_RESULT
    PREVIOUS_FRAME_RESULT = None
    # ---

    use_v2 = getattr(modules.globals, "map_faces", False)

    # Read target first
    try:
        target_frame = cv2.imread(target_path)
        if target_frame is None:
            update_status(f"Error: Could not read target image: {target_path}", NAME)
            return
    except Exception as read_e:
        update_status(f"Error reading target image {target_path}: {read_e}", NAME)
        return

    result = None
    try:
        if use_v2:
            if getattr(modules.globals, "many_faces", False):
                 update_status("Processing image with 'map_faces' and 'many_faces'. Using pre-analysis map.", NAME)
            # V2 processes based on global maps, doesn't need source_path here directly
            # Assumes maps are pre-populated. Pass target_path for map lookup.
            result = process_frame_v2(target_frame, target_path)

        else: # Simple mode
            try:
                source_img = cv2.imread(source_path)
                if source_img is None:
                    update_status(f"Error: Could not read source image: {source_path}", NAME)
                    return
                source_face = get_one_face(source_img)
                if not source_face:
                    update_status(f"Error: No face found in source image: {source_path}", NAME)
                    return
            except Exception as src_e:
                 update_status(f"Error reading or analyzing source image {source_path}: {src_e}", NAME)
                 return

            result = process_frame(source_face, target_frame)

        # Write the result if processing was successful
        if result is not None:
            write_success = cv2.imwrite(output_path, result)
            if write_success:
                update_status(f"Output image saved to: {output_path}", NAME)
            else:
                update_status(f"Error: Failed to write output image to {output_path}", NAME)
        else:
            # This case might occur if process_frame/v2 returns None unexpectedly
            update_status("Image processing failed (result was None).", NAME)

    except Exception as proc_e:
         update_status(f"Error during image processing: {proc_e}", NAME)