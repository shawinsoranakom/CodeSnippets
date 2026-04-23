def _processing_thread_func(capture_queue, processed_queue, stop_event,
                            camera_fps: float = 30.0):
    """Processing thread: takes raw frames from capture_queue, runs face
    detection (throttled), applies face swap/enhancement, and puts results
    into processed_queue.

    Args:
        camera_fps: Actual camera frame rate — used to compute how many
            frames to skip between face detections (~80ms target).
    """
    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    source_image = None
    last_source_path = None
    prev_time = time.time()
    fps_update_interval = 0.5
    frame_count = 0
    fps = 0
    det_count = 0
    cached_target_face = None
    cached_many_faces = None
    # Detect every N frames ≈ 80ms.  At 60fps → every 5 frames (83ms),
    # at 30fps → every 3 frames (100ms), at 15fps → every frame.
    det_interval = max(1, round(camera_fps * 0.08))

    while not stop_event.is_set():
        try:
            frame = capture_queue.get(timeout=0.05)
        except queue.Empty:
            continue

        temp_frame = frame

        if modules.globals.live_mirror:
            temp_frame = gpu_flip(temp_frame, 1)

        if not modules.globals.map_faces:
            if modules.globals.source_path and modules.globals.source_path != last_source_path:
                last_source_path = modules.globals.source_path
                source_image = get_one_face(cv2.imread(modules.globals.source_path))

            # Run detection every det_interval frames (~80ms).
            # Use fast detection (det-only, no landmark/recognition) for live mode.
            det_count += 1
            if det_count % det_interval == 0:
                if modules.globals.many_faces:
                    cached_target_face = None
                    cached_many_faces = detect_many_faces_fast(temp_frame)
                else:
                    cached_target_face = detect_one_face_fast(temp_frame)
                    cached_many_faces = None

            # Build face list for enhancers from cached detection
            _cached_faces = None
            if cached_many_faces:
                _cached_faces = cached_many_faces
            elif cached_target_face is not None:
                _cached_faces = [cached_target_face]

            for frame_processor in frame_processors:
                if frame_processor.NAME == "DLC.FACE-ENHANCER":
                    if modules.globals.fp_ui["face_enhancer"]:
                        temp_frame = frame_processor.process_frame(
                            None, temp_frame, detected_faces=_cached_faces)
                elif frame_processor.NAME == "DLC.FACE-ENHANCER-GPEN256":
                    if modules.globals.fp_ui.get("face_enhancer_gpen256", False):
                        temp_frame = frame_processor.process_frame(
                            None, temp_frame, detected_faces=_cached_faces)
                elif frame_processor.NAME == "DLC.FACE-ENHANCER-GPEN512":
                    if modules.globals.fp_ui.get("face_enhancer_gpen512", False):
                        temp_frame = frame_processor.process_frame(
                            None, temp_frame, detected_faces=_cached_faces)
                elif frame_processor.NAME == "DLC.FACE-SWAPPER":
                    # Use cached face positions from detection thread
                    swapped_bboxes = []
                    if modules.globals.many_faces and cached_many_faces:
                        result = temp_frame.copy()
                        for t_face in cached_many_faces:
                            result = frame_processor.swap_face(source_image, t_face, result)
                            if hasattr(t_face, 'bbox') and t_face.bbox is not None:
                                swapped_bboxes.append(t_face.bbox.astype(int))
                        temp_frame = result
                    elif cached_target_face is not None:
                        temp_frame = frame_processor.swap_face(source_image, cached_target_face, temp_frame)
                        if hasattr(cached_target_face, 'bbox') and cached_target_face.bbox is not None:
                            swapped_bboxes.append(cached_target_face.bbox.astype(int))
                    # Apply post-processing (sharpening, interpolation)
                    temp_frame = frame_processor.apply_post_processing(temp_frame, swapped_bboxes)
                else:
                    temp_frame = frame_processor.process_frame(source_image, temp_frame)
        else:
            modules.globals.target_path = None
            for frame_processor in frame_processors:
                if frame_processor.NAME == "DLC.FACE-ENHANCER":
                    if modules.globals.fp_ui["face_enhancer"]:
                        temp_frame = frame_processor.process_frame_v2(temp_frame)
                elif frame_processor.NAME in ("DLC.FACE-ENHANCER-GPEN256", "DLC.FACE-ENHANCER-GPEN512"):
                    fp_key = frame_processor.NAME.split(".")[-1].lower().replace("-", "_")
                    if modules.globals.fp_ui.get(fp_key, False):
                        temp_frame = frame_processor.process_frame_v2(temp_frame)
                else:
                    temp_frame = frame_processor.process_frame_v2(temp_frame)

        # Calculate and display FPS
        current_time = time.time()
        frame_count += 1
        if current_time - prev_time >= fps_update_interval:
            fps = frame_count / (current_time - prev_time)
            frame_count = 0
            prev_time = current_time

        if modules.globals.show_fps:
            cv2.putText(
                temp_frame,
                f"FPS: {fps:.1f}",
                (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX,
                1,
                (0, 255, 0),
                2,
            )

        # Queue the processed frame as BGR; the display thread resizes to the
        # preview window first and then runs cvtColor on the (much smaller)
        # buffer — cheaper than converting the full 1080p frame here.
        try:
            processed_queue.put_nowait(temp_frame)
        except queue.Full:
            try:
                processed_queue.get_nowait()
            except queue.Empty:
                pass
            try:
                processed_queue.put_nowait(temp_frame)
            except queue.Full:
                pass