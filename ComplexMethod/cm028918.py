def swap_face(source_face: Face, target_face: Face, temp_frame: Frame) -> Frame:
    """Optimized face swapping with better memory management and performance."""
    face_swapper = get_face_swapper()
    if face_swapper is None:
        update_status("Face swapper model not loaded or failed to load. Skipping swap.", NAME)
        return temp_frame

    # Safety check for faces
    if source_face is None or target_face is None:
        return temp_frame
    if not hasattr(source_face, 'normed_embedding') or source_face.normed_embedding is None:
        return temp_frame

    # _fast_paste_back writes in-place on the GPU path.  Only copy when
    # mouth_mask or opacity < 1 need an unmodified original.
    opacity = getattr(modules.globals, "opacity", 1.0)
    opacity = max(0.0, min(1.0, opacity))
    mouth_mask_enabled = getattr(modules.globals, "mouth_mask", False)
    needs_original = opacity < 1.0 or mouth_mask_enabled
    if needs_original:
        original_frame = temp_frame.copy()
    else:
        original_frame = temp_frame

    if temp_frame.dtype != np.uint8:
        temp_frame = np.clip(temp_frame, 0, 255).astype(np.uint8)

    try:
        if not temp_frame.flags['C_CONTIGUOUS']:
            temp_frame = np.ascontiguousarray(temp_frame)

        # Use paste_back=False and our optimized paste-back
        if any("DmlExecutionProvider" in p for p in modules.globals.execution_providers):
            with modules.globals.dml_lock:
                bgr_fake, M = face_swapper.get(
                    temp_frame, target_face, source_face, paste_back=False
                )
        else:
            bgr_fake, M = face_swapper.get(
                temp_frame, target_face, source_face, paste_back=False
            )

        if bgr_fake is None:
            return original_frame

        if not isinstance(bgr_fake, np.ndarray):
            return original_frame

        # Pass a dummy aimg with correct shape — _fast_paste_back only uses aimg.shape
        # to create the white mask. Avoids redundant norm_crop2 (~0.6ms).
        _face_size = face_swapper.input_size[0]
        _aimg_dummy = np.empty((_face_size, _face_size, 3), dtype=np.uint8)

        swapped_frame = _fast_paste_back(temp_frame, bgr_fake, _aimg_dummy, M)

    except Exception as e:
        print(f"Error during face swap: {e}")
        return original_frame

    # --- Post-swap Processing (Masking, Opacity, etc.) ---
    # Now, work with the guaranteed uint8 'swapped_frame'

    if mouth_mask_enabled: # Check if mouth_mask is enabled
        # Create a mask for the target face
        face_mask = create_face_mask(target_face, original_frame) # Use original_frame for mask creation geometry

        # Create the mouth mask using the ORIGINAL frame (before swap) for cutout
        mouth_mask, mouth_cutout, mouth_box, lower_lip_polygon = (
            create_lower_mouth_mask(target_face, original_frame) # Use original_frame for real mouth cutout
        )

        # Apply the mouth area only if mouth_cutout exists
        if mouth_cutout is not None and mouth_box != (0,0,0,0):
            # Apply mouth area (from original) onto the 'swapped_frame'
            swapped_frame = apply_mouth_area(
                swapped_frame, mouth_cutout, mouth_box, face_mask, lower_lip_polygon
            )

            # Draw bounding box only while slider is being dragged
            if getattr(modules.globals, "show_mouth_mask_box", False):
                mouth_mask_data = (mouth_mask, mouth_cutout, mouth_box, lower_lip_polygon)
                swapped_frame = draw_mouth_mask_visualization(
                    swapped_frame, target_face, mouth_mask_data
                )

    # --- Poisson Blending ---
    if getattr(modules.globals, "poisson_blend", False):
        face_mask = create_face_mask(target_face, temp_frame)
        if face_mask is not None:
            # Find bounding box of the mask
            y_indices, x_indices = np.where(face_mask > 0)
            if len(x_indices) > 0 and len(y_indices) > 0:
                x_min, x_max = np.min(x_indices), np.max(x_indices)
                y_min, y_max = np.min(y_indices), np.max(y_indices)

                # Calculate center
                center = (int((x_min + x_max) / 2), int((y_min + y_max) / 2))

                # Crop src and mask
                src_crop = swapped_frame[y_min : y_max + 1, x_min : x_max + 1]
                mask_crop = face_mask[y_min : y_max + 1, x_min : x_max + 1]

                try:
                    # Use original_frame as destination to blend the swapped face onto it
                    swapped_frame = cv2.seamlessClone(
                        src_crop,
                        original_frame,
                        mask_crop,
                        center,
                        cv2.NORMAL_CLONE,
                    )
                except Exception as e:
                    print(f"Poisson blending failed: {e}")

    # Apply opacity blend between the original frame and the swapped frame
    if opacity >= 1.0:
        return swapped_frame.astype(np.uint8)

    # Blend the original_frame with the (potentially mouth-masked) swapped_frame
    final_swapped_frame = gpu_add_weighted(original_frame.astype(np.uint8), 1 - opacity, swapped_frame.astype(np.uint8), opacity, 0)
    return final_swapped_frame.astype(np.uint8)