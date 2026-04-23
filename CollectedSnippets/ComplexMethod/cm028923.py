def process_frames(
    source_path: str, temp_frame_paths: List[str], progress: Any = None
) -> None:
    """
    Processes a list of frame paths (typically for video).
    Optimized with better memory management and caching.
    Iterates through frames, applies the appropriate swapping logic based on globals,
    and saves the result back to the frame path. Handles multi-threading via caller.
    """
    # Determine which processing function to use based on map_faces global setting
    use_v2 = getattr(modules.globals, "map_faces", False)
    source_face = None # Initialize source_face

    # --- Pre-load source face only if needed (Simple Mode: map_faces=False) ---
    if not use_v2:
        if not source_path or not os.path.exists(source_path):
            update_status(f"Error: Source path invalid or not provided for simple mode: {source_path}", NAME)
            # Log the error but allow proceeding; subsequent check will stop processing.
        else:
            try:
                source_img = cv2.imread(source_path)
                if source_img is None:
                    # Specific error for file reading failure
                    update_status(f"Error reading source image file {source_path}. Please check the path and file integrity.", NAME)
                else:
                    source_face = get_one_face(source_img)
                    if source_face is None:
                        # Specific message for no face detected after successful read
                        update_status(f"Warning: Successfully read source image {source_path}, but no face was detected. Swaps will be skipped.", NAME)
                    # Free memory immediately after extracting face
                    del source_img
            except Exception as e:
                # Print the specific exception caught
                import traceback
                print(f"{NAME}: Caught exception during source image processing for {source_path}:")
                traceback.print_exc() # Print the full traceback
                update_status(f"Error during source image reading or analysis {source_path}: {e}", NAME)
                # Log general exception during the process

    total_frames = len(temp_frame_paths)
    # update_status(f"Processing {total_frames} frames. Use V2 (map_faces): {use_v2}", NAME) # Optional Debug

    # --- Stop processing entirely if in Simple Mode and source face is invalid ---
    if not use_v2 and source_face is None:
        update_status(f"Halting video processing: Invalid or no face detected in source image for simple mode.", NAME)
        if progress:
            # Ensure the progress bar completes if it was started
            remaining_updates = total_frames - progress.n if hasattr(progress, 'n') else total_frames
            if remaining_updates > 0:
                progress.update(remaining_updates)
        return # Exit the function entirely

    # --- Process each frame path provided in the list ---
    # Note: In the current core.py multi_process_frame, temp_frame_paths will usually contain only ONE path per call.
    for i, temp_frame_path in enumerate(temp_frame_paths):
        # update_status(f"Processing frame {i+1}/{total_frames}: {os.path.basename(temp_frame_path)}", NAME) # Optional Debug

        # Read the target frame
        temp_frame = None
        try:
            temp_frame = cv2.imread(temp_frame_path)
            if temp_frame is None:
                print(f"{NAME}: Error: Could not read frame: {temp_frame_path}, skipping.")
                if progress: progress.update(1)
                continue # Skip this frame if read fails
        except Exception as read_e:
            print(f"{NAME}: Error reading frame {temp_frame_path}: {read_e}, skipping.")
            if progress: progress.update(1)
            continue

        # Select processing function and execute
        result_frame = None
        try:
            if use_v2:
                # V2 uses global maps and needs the frame path for lookup in video mode
                # update_status(f"Using process_frame_v2 for: {os.path.basename(temp_frame_path)}", NAME) # Optional Debug
                result_frame = process_frame_v2(temp_frame, temp_frame_path)
            else:
                # Simple mode uses the pre-loaded source_face (already checked for validity above)
                # update_status(f"Using process_frame (simple) for: {os.path.basename(temp_frame_path)}", NAME) # Optional Debug
                result_frame = process_frame(source_face, temp_frame) # source_face is guaranteed to be valid here

            # Check if processing actually returned a frame
            if result_frame is None:
                 print(f"{NAME}: Warning: Processing returned None for frame {temp_frame_path}. Using original.")
                 result_frame = temp_frame

        except Exception as proc_e:
            print(f"{NAME}: Error processing frame {temp_frame_path}: {proc_e}")
            # import traceback # Optional for detailed debugging
            # traceback.print_exc()
            result_frame = temp_frame # Use original frame on processing error

        # Write the result back to the same frame path with optimized compression
        try:
            # Use PNG compression level 3 (faster) instead of default 9
            write_success = cv2.imwrite(temp_frame_path, result_frame, [cv2.IMWRITE_PNG_COMPRESSION, 3])
            if not write_success:
                print(f"{NAME}: Error: Failed to write processed frame to {temp_frame_path}")
        except Exception as write_e:
            print(f"{NAME}: Error writing frame {temp_frame_path}: {write_e}")

        # Free memory immediately after processing
        del temp_frame
        if result_frame is not None:
            del result_frame

        # Update progress bar
        if progress:
            progress.update(1)