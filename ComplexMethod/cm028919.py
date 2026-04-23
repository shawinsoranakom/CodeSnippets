def get_faces_optimized(frame: Frame, use_cache: bool = True) -> Optional[List[Face]]:
    """Optimized face detection for live mode on Apple Silicon"""
    global LAST_DETECTION_TIME, FACE_DETECTION_CACHE

    if not use_cache or not IS_APPLE_SILICON:
        # Standard detection
        if modules.globals.many_faces:
            return get_many_faces(frame)
        else:
            face = get_one_face(frame)
            return [face] if face else None

    # Adaptive detection rate for live mode
    current_time = time.time()
    time_since_last = current_time - LAST_DETECTION_TIME

    # Skip detection if too soon (adaptive frame skipping)
    if time_since_last < DETECTION_INTERVAL and FACE_DETECTION_CACHE:
        return FACE_DETECTION_CACHE.get('faces')

    # Perform detection
    LAST_DETECTION_TIME = current_time
    if modules.globals.many_faces:
        faces = get_many_faces(frame)
    else:
        face = get_one_face(frame)
        faces = [face] if face else None

    # Cache results
    FACE_DETECTION_CACHE['faces'] = faces
    FACE_DETECTION_CACHE['timestamp'] = current_time

    return faces