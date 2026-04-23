def enhance_face(temp_frame: Frame, detected_faces=None) -> Frame:
    """Enhances all faces in a frame using the GFPGAN ONNX model.

    Args:
        detected_faces: Pre-detected face list. When provided, skips
            the internal detection call (saves ~15-20ms per frame).
            Also enables temporal caching — inference runs every
            _ENH_INTERVAL frames, reusing the cached result otherwise.
    """
    session = get_face_enhancer()

    # Determine model input resolution from the session metadata
    input_info = session.get_inputs()[0]
    input_name = input_info.name
    input_shape = input_info.shape  # e.g. [1, 3, 512, 512]
    try:
        align_size = int(input_shape[2])
        if align_size <= 0:
            align_size = 512
    except (ValueError, TypeError, IndexError):
        align_size = 512

    # Use pre-detected faces if available, otherwise detect
    faces = detected_faces if detected_faces is not None else get_many_faces(temp_frame)
    if not faces:
        return temp_frame

    # Temporal caching: only available when faces are pre-detected (live mode)
    # AND we're in single-face mode — the cache holds exactly one enhancement,
    # so reusing it in many_faces mode would paste the same face onto every
    # detected target.
    many_faces_mode = getattr(modules.globals, "many_faces", False)
    use_cache = detected_faces is not None and not many_faces_mode
    if use_cache:
        _enh_live_cache['frame_count'] += 1
        run_inference_this_frame = (_enh_live_cache['frame_count'] % _ENH_INTERVAL == 0
                                   or _enh_live_cache['enhanced_bgr'] is None)
    else:
        run_inference_this_frame = True

    for face in faces:
        if not hasattr(face, "kps") or face.kps is None:
            continue

        landmarks_5 = face.kps.astype(np.float32)
        if landmarks_5.shape[0] < 5:
            continue

        if run_inference_this_frame:
            aligned_face, affine_matrix = _align_face(
                temp_frame, landmarks_5, output_size=align_size
            )
            if aligned_face is None or affine_matrix is None:
                continue

            try:
                with THREAD_SEMAPHORE:
                    from modules.processors.frame._onnx_enhancer import (
                        run_inference,
                    )
                    input_tensor = _preprocess_face(aligned_face)
                    output_tensor = run_inference(session, input_name, input_tensor)
                    enhanced_bgr = _postprocess_face(output_tensor)

                eh, ew = enhanced_bgr.shape[:2]
                if eh != align_size or ew != align_size:
                    enhanced_bgr = cv2.resize(
                        enhanced_bgr,
                        (align_size, align_size),
                        interpolation=cv2.INTER_LANCZOS4,
                    )

                # Cache for reuse on next frame
                if use_cache:
                    _enh_live_cache['enhanced_bgr'] = enhanced_bgr
                    _enh_live_cache['affine_matrix'] = affine_matrix
                    _enh_live_cache['align_size'] = align_size

                _paste_back(
                    temp_frame, enhanced_bgr, affine_matrix, output_size=align_size
                )
            except Exception as e:
                print(f"{NAME}: Error enhancing a face: {e}")
                continue
        else:
            # Reuse cached enhanced face — just paste back onto current frame
            cached = _enh_live_cache
            if cached['enhanced_bgr'] is not None:
                _paste_back(
                    temp_frame, cached['enhanced_bgr'],
                    cached['affine_matrix'],
                    output_size=cached['align_size'],
                )
        if not many_faces_mode:
            break  # single-face live mode — only process first face

    return temp_frame