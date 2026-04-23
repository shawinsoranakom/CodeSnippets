def iter_segment_frames(camera_paths, start_time, end_time, fps=20, use_qcam=False, frame_size: tuple[int, int] | None = None):
  frames_per_seg = fps * 60
  start_frame, end_frame = int(start_time * fps), int(end_time * fps)
  current_seg: int = -1
  seg_frames: FrameReader | np.ndarray | None = None

  for global_idx in range(start_frame, end_frame):
    seg_idx, local_idx = global_idx // frames_per_seg, global_idx % frames_per_seg

    if seg_idx != current_seg:
      current_seg = seg_idx
      path = camera_paths[seg_idx] if seg_idx < len(camera_paths) else None
      if not path:
        raise RuntimeError(f"No camera file for segment {seg_idx}")

      if use_qcam:
        w, h = frame_size or get_frame_dimensions(path)
        with FileReader(path) as f:
          result = subprocess.run(["ffmpeg", "-v", "quiet", "-i", "-", "-f", "rawvideo", "-pix_fmt", "nv12", "-"],
                                  input=f.read(), capture_output=True)
        if result.returncode != 0:
          raise RuntimeError(f"ffmpeg failed: {result.stderr.decode()}")
        seg_frames = np.frombuffer(result.stdout, dtype=np.uint8).reshape(-1, w * h * 3 // 2)
      else:
        seg_frames = FrameReader(path, pix_fmt="nv12")

    assert seg_frames is not None
    frame = seg_frames[local_idx] if use_qcam else seg_frames.get(local_idx)
    yield global_idx, frame