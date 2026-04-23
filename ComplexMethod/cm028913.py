def _run_pipe_pipeline(
    target_path: str,
    temp_output_path: str,
    fps: float,
    source_face: Any,
    frame_processors: List[Any],
    width: int,
    height: int,
    frame_size: int,
    total_frames: int,
    encoder: str,
    encoder_options: List[str],
) -> bool:
    """Run the FFmpeg-pipe read → process → encode pipeline once."""

    # --- Reader: decode source video to raw BGR24 on stdout ---
    reader_cmd = [
        'ffmpeg', '-hide_banner',
        '-hwaccel', 'auto',
        '-i', target_path,
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-v', 'error',
        '-',
    ]

    # --- Writer: encode raw BGR24 from stdin ---
    writer_cmd = [
        'ffmpeg', '-hide_banner',
        '-f', 'rawvideo',
        '-pix_fmt', 'bgr24',
        '-s', f'{width}x{height}',
        '-r', str(fps),
        '-i', '-',
        '-c:v', encoder,
    ]
    writer_cmd.extend(encoder_options)
    writer_cmd.extend([
        '-pix_fmt', 'yuv420p',
        '-movflags', '+faststart',
        '-vf', 'colorspace=bt709:iall=bt601-6-625:fast=1',
        '-v', 'error',
        '-y', temp_output_path,
    ])

    reader = None
    writer = None
    try:
        reader = subprocess.Popen(
            reader_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
        writer = subprocess.Popen(
            writer_cmd, stdin=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except Exception as e:
        print(f"[DLC.CORE] Failed to start FFmpeg pipes: {e}")
        for proc in (reader, writer):
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass
        return False

    processed_count = 0
    bar_fmt = ('{l_bar}{bar}| {n_fmt}/{total_fmt} '
               '[{elapsed}<{remaining}, {rate_fmt}{postfix}]')

    try:
        with tqdm(total=total_frames, desc='Processing', unit='frame',
                  dynamic_ncols=True, bar_format=bar_fmt) as progress:
            progress.set_postfix({
                'execution_providers': modules.globals.execution_providers,
                'threads': modules.globals.execution_threads,
                'mode': 'in-memory',
            })

            # Pipelined detection: while processing frame N (swap on
            # ANE), start detecting the face in the next frame
            # (detection on GPU).  They use different hardware units
            # so the work overlaps.
            detect_executor = ThreadPoolExecutor(max_workers=1)
            pending_detect = None
            use_pipeline = not modules.globals.many_faces

            while True:
                raw = reader.stdout.read(frame_size)
                if len(raw) != frame_size:
                    break

                frame = np.frombuffer(raw, dtype=np.uint8).reshape(
                    (height, width, 3)
                ).copy()

                # Get the detection result for THIS frame
                if use_pipeline:
                    if pending_detect is not None:
                        target_face = pending_detect.result()
                    else:
                        target_face = get_one_face(frame)
                    # Start detecting on THIS frame eagerly — the result
                    # will be used for the next iteration.  At video
                    # frame rates the face barely moves between frames.
                    # Hand the detector its own copy: the frame processors
                    # below mutate `frame` in place (paste-back), which
                    # would otherwise race with detection.
                    pending_detect = detect_executor.submit(
                        get_one_face, frame.copy())
                else:
                    target_face = None

                # Run frame through every active processor
                for fp in frame_processors:
                    try:
                        frame = fp.process_frame(source_face, frame, target_face=target_face)
                    except TypeError:
                        frame = fp.process_frame(source_face, frame)

                writer.stdin.write(frame.tobytes())
                processed_count += 1
                progress.update(1)

            detect_executor.shutdown(wait=True)

        # Graceful shutdown
        writer.stdin.close()
        writer.wait()
        reader.wait()

        if writer.returncode != 0:
            stderr_out = writer.stderr.read().decode(errors='ignore').strip()
            if stderr_out:
                print(f"[DLC.CORE] FFmpeg encoder error: {stderr_out}")
            return False

        return processed_count > 0 and os.path.isfile(temp_output_path)

    except BrokenPipeError:
        print("[DLC.CORE] FFmpeg pipe broken (encoder may not be available).")
        return False
    except Exception as e:
        print(f"[DLC.CORE] In-memory processing error: {e}")
        return False
    finally:
        for proc in (reader, writer):
            if proc:
                try:
                    proc.kill()
                except Exception:
                    pass