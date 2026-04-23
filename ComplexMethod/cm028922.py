def process_frame_v2(temp_frame: Frame, temp_frame_path: str = "") -> Frame:
    """Handles complex mapping scenarios (map_faces=True) and live streams."""
    if getattr(modules.globals, "opacity", 1.0) == 0:
        # If opacity is 0, no swap happens, so no post-processing needed.
        # Also reset interpolation state if it was active.
        global PREVIOUS_FRAME_RESULT
        PREVIOUS_FRAME_RESULT = None
        return temp_frame

    processed_frame = temp_frame # Start with the input frame
    swapped_face_bboxes = [] # Keep track of where swaps happened

    # Determine source/target pairs based on mode
    source_target_pairs = []

    # Ensure maps exist before accessing them
    source_target_map = getattr(modules.globals, "source_target_map", None)
    simple_map = getattr(modules.globals, "simple_map", None)

    # Check if target is a file path (image or video) or live stream
    is_file_target = modules.globals.target_path and (is_image(modules.globals.target_path) or is_video(modules.globals.target_path))

    if is_file_target:
        # Processing specific image or video file with pre-analyzed maps
        if source_target_map:
            if modules.globals.many_faces:
                source_face = default_source_face() # Use default source for all targets
                if source_face:
                    for map_data in source_target_map:
                        if is_image(modules.globals.target_path):
                            target_info = map_data.get("target", {})
                            if target_info: # Check if target info exists
                                target_face = target_info.get("face")
                                if target_face:
                                    source_target_pairs.append((source_face, target_face))
                        elif is_video(modules.globals.target_path):
                             # Find faces for the current frame_path in video map
                             target_frames_data = map_data.get("target_faces_in_frame", [])
                             if target_frames_data: # Check if frame data exists
                                 target_frames = [f for f in target_frames_data if f and f.get("location") == temp_frame_path]
                                 for frame_data in target_frames:
                                     faces_in_frame = frame_data.get("faces", [])
                                     if faces_in_frame: # Check if faces exist
                                         for target_face in faces_in_frame:
                                             source_target_pairs.append((source_face, target_face))
            else: # Single face or specific mapping
                 for map_data in source_target_map:
                    source_info = map_data.get("source", {})
                    if not source_info: continue # Skip if no source info
                    source_face = source_info.get("face")
                    if not source_face: continue # Skip if no source defined for this map entry

                    if is_image(modules.globals.target_path):
                        target_info = map_data.get("target", {})
                        if target_info:
                           target_face = target_info.get("face")
                           if target_face:
                              source_target_pairs.append((source_face, target_face))
                    elif is_video(modules.globals.target_path):
                        target_frames_data = map_data.get("target_faces_in_frame", [])
                        if target_frames_data:
                           target_frames = [f for f in target_frames_data if f and f.get("location") == temp_frame_path]
                           for frame_data in target_frames:
                               faces_in_frame = frame_data.get("faces", [])
                               if faces_in_frame:
                                  for target_face in faces_in_frame:
                                      source_target_pairs.append((source_face, target_face))

    else:
        # Live stream or webcam processing (analyze faces on the fly)
        detected_faces = get_many_faces(processed_frame)
        if detected_faces:
            if modules.globals.many_faces:
                 source_face = default_source_face() # Use default source for all detected targets
                 if source_face:
                     for target_face in detected_faces:
                        source_target_pairs.append((source_face, target_face))
            elif simple_map:
                # Use simple_map (source_faces <-> target_embeddings)
                source_faces = simple_map.get("source_faces", [])
                target_embeddings = simple_map.get("target_embeddings", [])

                if source_faces and target_embeddings and len(source_faces) == len(target_embeddings):
                     # Match detected faces to the closest target embedding
                     if len(detected_faces) <= len(target_embeddings):
                          # More targets defined than detected - match each detected face
                          for detected_face in detected_faces:
                              if detected_face.normed_embedding is None: continue
                              closest_idx, _ = find_closest_centroid(target_embeddings, detected_face.normed_embedding)
                              if 0 <= closest_idx < len(source_faces):
                                  source_target_pairs.append((source_faces[closest_idx], detected_face))
                     else:
                          # More faces detected than targets defined - match each target embedding to closest detected face
                          detected_embeddings = [f.normed_embedding for f in detected_faces if f.normed_embedding is not None]
                          detected_faces_with_embedding = [f for f in detected_faces if f.normed_embedding is not None]
                          if not detected_embeddings: return processed_frame # No embeddings to match

                          for i, target_embedding in enumerate(target_embeddings):
                              if 0 <= i < len(source_faces): # Ensure source face exists for this embedding
                                 closest_idx, _ = find_closest_centroid(detected_embeddings, target_embedding)
                                 if 0 <= closest_idx < len(detected_faces_with_embedding):
                                     source_target_pairs.append((source_faces[i], detected_faces_with_embedding[closest_idx]))
            else: # Fallback: if no map, use default source for the single detected face (if any)
                source_face = default_source_face()
                target_face = get_one_face(processed_frame, detected_faces) # Use faces already detected
                if source_face and target_face:
                    source_target_pairs.append((source_face, target_face))


    # Perform swaps based on the collected pairs
    current_swap_target = processed_frame.copy() # Apply swaps sequentially
    for source_face, target_face in source_target_pairs:
        if source_face and target_face:
            current_swap_target = swap_face(source_face, target_face, current_swap_target)
            if target_face is not None and hasattr(target_face, "bbox") and target_face.bbox is not None:
                swapped_face_bboxes.append(target_face.bbox.astype(int))
    processed_frame = current_swap_target # Assign final result


    # Apply sharpening and interpolation
    final_frame = apply_post_processing(processed_frame, swapped_face_bboxes)

    return final_frame