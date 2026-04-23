def process_video_in_memory(source_path: str, target_path: str, fps: float) -> bool:
    """Process video frames in-memory using FFmpeg pipes, eliminating disk I/O.

    Reads raw frames from the source video via an FFmpeg decoder pipe, runs each
    frame through all active frame processors sequentially, and writes the
    result directly to an FFmpeg encoder pipe.  This avoids extracting frames to
    PNG on disk, which is the biggest I/O bottleneck in the disk-based pipeline.

    Returns True on success, False on failure (caller should fall back to the
    disk-based pipeline).
    """
    import cv2
    from modules.face_analyser import get_one_face
    from modules.utilities import (
        get_video_dimensions,
        estimate_frame_count,
        get_temp_output_path,
    )

    temp_output_path = get_temp_output_path(target_path)

    # --- Pre-load source face (needed by face_swapper in simple mode) ---
    source_face = None
    if source_path and os.path.exists(source_path):
        source_img = cv2.imread(source_path)
        if source_img is not None:
            source_face = get_one_face(source_img)
            del source_img
        if source_face is None:
            print("[DLC.CORE] Warning: No face detected in source image. "
                  "Face swapping will be skipped.")

    # --- Collect frame processors & reset per-video state ---
    frame_processors = get_frame_processors_modules(modules.globals.frame_processors)
    for fp in frame_processors:
        if hasattr(fp, 'PREVIOUS_FRAME_RESULT'):
            fp.PREVIOUS_FRAME_RESULT = None

    # --- Video metadata ---
    try:
        width, height = get_video_dimensions(target_path)
    except Exception as e:
        print(f"[DLC.CORE] Failed to get video dimensions: {e}")
        return False

    total_frames = estimate_frame_count(target_path, fps)
    frame_size = width * height * 3

    # --- Build encoder arguments ---
    encoder = modules.globals.video_encoder
    encoder_options: List[str] = []
    is_hw_encoder = False

    if 'CUDAExecutionProvider' in modules.globals.execution_providers:
        if encoder == 'libx264':
            encoder = 'h264_nvenc'
            is_hw_encoder = True
            encoder_options = [
                '-preset', 'p4', '-tune', 'hq', '-rc', 'vbr',
                '-cq', str(modules.globals.video_quality), '-b:v', '0',
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_nvenc'
            is_hw_encoder = True
            encoder_options = [
                '-preset', 'p4', '-tune', 'hq', '-rc', 'vbr',
                '-cq', str(modules.globals.video_quality), '-b:v', '0',
            ]
    elif 'DmlExecutionProvider' in modules.globals.execution_providers:
        if encoder == 'libx264':
            encoder = 'h264_amf'
            is_hw_encoder = True
            encoder_options = [
                '-quality', 'quality', '-rc', 'vbr_latency',
                '-qp_i', str(modules.globals.video_quality),
                '-qp_p', str(modules.globals.video_quality),
            ]
        elif encoder == 'libx265':
            encoder = 'hevc_amf'
            is_hw_encoder = True
            encoder_options = [
                '-quality', 'quality', '-rc', 'vbr_latency',
                '-qp_i', str(modules.globals.video_quality),
                '-qp_p', str(modules.globals.video_quality),
            ]

    if not is_hw_encoder:
        if encoder == 'libx264':
            encoder_options = [
                '-preset', 'medium',
                '-crf', str(modules.globals.video_quality),
                '-tune', 'film',
            ]
        elif encoder == 'libx265':
            encoder_options = [
                '-preset', 'medium',
                '-crf', str(modules.globals.video_quality),
                '-x265-params', 'log-level=error',
            ]
        elif encoder == 'libvpx-vp9':
            encoder_options = [
                '-crf', str(modules.globals.video_quality),
                '-b:v', '0', '-cpu-used', '2',
            ]

    # --- Attempt pipeline (hw encoder first, then sw fallback) ---
    encoders_to_try = [(encoder, encoder_options)]
    if is_hw_encoder:
        # Software fallback
        sw_encoder = 'libx264'
        sw_options = [
            '-preset', 'medium',
            '-crf', str(modules.globals.video_quality),
            '-tune', 'film',
        ]
        encoders_to_try.append((sw_encoder, sw_options))

    for attempt, (enc, enc_opts) in enumerate(encoders_to_try):
        # Reset interpolation state on retry
        if attempt > 0:
            for fp in frame_processors:
                if hasattr(fp, 'PREVIOUS_FRAME_RESULT'):
                    fp.PREVIOUS_FRAME_RESULT = None

        success = _run_pipe_pipeline(
            target_path, temp_output_path, fps,
            source_face, frame_processors,
            width, height, frame_size, total_frames,
            enc, enc_opts,
        )
        if success:
            return True

        if attempt == 0 and is_hw_encoder:
            print(f"[DLC.CORE] Hardware encoder '{enc}' failed, "
                  f"retrying with software encoder...")

    return False