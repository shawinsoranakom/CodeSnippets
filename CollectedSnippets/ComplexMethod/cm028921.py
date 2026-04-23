def process_frame(source_face: Face, temp_frame: Frame, target_face: Face = None) -> Frame:
    """Process a single frame, swapping source_face onto detected target(s).

    Args:
        target_face: Pre-detected target face. When provided, skips the
            internal face detection call (saves ~30-40ms per frame).
            Ignored when many_faces mode is active.
    """
    if getattr(modules.globals, "opacity", 1.0) == 0:
        global PREVIOUS_FRAME_RESULT
        PREVIOUS_FRAME_RESULT = None
        return temp_frame

    processed_frame = temp_frame
    swapped_face_bboxes = []

    if modules.globals.many_faces:
        many_faces = get_many_faces(processed_frame)
        if many_faces:
            current_swap_target = processed_frame.copy()
            for face in many_faces:
                current_swap_target = swap_face(source_face, face, current_swap_target)
                if face is not None and hasattr(face, "bbox") and face.bbox is not None:
                    swapped_face_bboxes.append(face.bbox.astype(int))
            processed_frame = current_swap_target
    else:
        if target_face is None:
            target_face = get_one_face(processed_frame)
        if target_face:
            processed_frame = swap_face(source_face, target_face, processed_frame)
            if hasattr(target_face, "bbox") and target_face.bbox is not None:
                swapped_face_bboxes.append(target_face.bbox.astype(int))

    final_frame = apply_post_processing(processed_frame, swapped_face_bboxes)
    return final_frame