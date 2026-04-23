def start() -> None:
    """Start processing with performance monitoring."""
    import time

    start_time = time.time()

    for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
        if not frame_processor.pre_start():
            return
    update_status('Processing...')

    # process image to image
    if has_image_extension(modules.globals.target_path):
        if modules.globals.nsfw_filter and ui.check_and_ignore_nsfw(modules.globals.target_path, destroy):
            return
        try:
            shutil.copy2(modules.globals.target_path, modules.globals.output_path)
        except Exception as e:
            print("Error copying file:", str(e))
        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_image(modules.globals.source_path, modules.globals.output_path, modules.globals.output_path)
            release_resources()
        if is_image(modules.globals.target_path):
            elapsed = time.time() - start_time
            update_status(f'Processing to image succeed! (Time: {elapsed:.2f}s)')
        else:
            update_status('Processing to image failed!')
        return

    # process image to videos
    if modules.globals.nsfw_filter and ui.check_and_ignore_nsfw(modules.globals.target_path, destroy):
        return

    # Detect FPS early (needed by both pipelines)
    if modules.globals.keep_fps:
        update_status('Detecting fps...')
        fps = detect_fps(modules.globals.target_path)
    else:
        fps = 30.0

    video_created = False

    # --- In-memory pipeline (non-map_faces only) ---
    # Reads frames from FFmpeg pipe, processes in memory, encodes directly.
    # Eliminates all per-frame PNG disk I/O for a major speed-up.
    if not modules.globals.map_faces:
        update_status(f'Processing video in-memory at {fps} fps...')
        create_temp(modules.globals.target_path)

        processing_start = time.time()
        video_created = process_video_in_memory(
            modules.globals.source_path,
            modules.globals.target_path,
            fps,
        )
        processing_time = time.time() - processing_start
        release_resources()

        if video_created:
            update_status(f'In-memory processing + encoding completed in {processing_time:.2f}s')

    # --- Disk-based fallback (required for map_faces, or if pipe failed) ---
    if not video_created:
        if not modules.globals.map_faces:
            update_status('Falling back to disk-based processing...')

        extraction_start = time.time()
        if not modules.globals.map_faces:
            create_temp(modules.globals.target_path)
            update_status('Extracting frames...')
            extract_frames(modules.globals.target_path)
        extraction_time = time.time() - extraction_start

        temp_frame_paths = get_temp_frame_paths(modules.globals.target_path)
        total_frames = len(temp_frame_paths)
        update_status(f'Processing {total_frames} frames with {modules.globals.execution_threads} threads...')

        processing_start = time.time()
        for frame_processor in get_frame_processors_modules(modules.globals.frame_processors):
            update_status('Progressing...', frame_processor.NAME)
            frame_processor.process_video(modules.globals.source_path, temp_frame_paths)
            release_resources()
        processing_time = time.time() - processing_start
        fps_processing = total_frames / processing_time if processing_time > 0 else 0
        update_status(f'Frame processing completed in {processing_time:.2f}s ({fps_processing:.2f} fps)')

        encoding_start = time.time()
        update_status(f'Creating video with {fps} fps...')
        video_created = create_video(modules.globals.target_path, fps)
        encoding_time = time.time() - encoding_start
        if video_created:
            update_status(f'Video encoding completed in {encoding_time:.2f}s')

    if not video_created:
        update_status('Video encoding failed. No temporary output video was created.')
        clean_temp(modules.globals.target_path)
        return

    # handle audio
    if modules.globals.keep_audio:
        if modules.globals.keep_fps:
            update_status('Restoring audio...')
        else:
            update_status('Restoring audio might cause issues as fps are not kept...')
        restore_audio(modules.globals.target_path, modules.globals.output_path)
    else:
        move_temp(modules.globals.target_path, modules.globals.output_path)

    # clean and validate
    clean_temp(modules.globals.target_path)

    total_time = time.time() - start_time
    if is_video(modules.globals.target_path) and modules.globals.output_path and os.path.isfile(modules.globals.output_path):
        update_status(f'Video processing succeeded! Total time: {total_time:.2f}s')
    else:
        update_status('Processing to video failed!')