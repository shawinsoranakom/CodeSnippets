def video_to_ndarrays(path: str, num_frames: int = -1) -> npt.NDArray:
    import cv2

    cap = cv2.VideoCapture(path)
    if not cap.isOpened():
        raise ValueError(f"Could not open video file {path}")

    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    frames = []

    num_frames = num_frames if num_frames > 0 else total_frames
    frame_indices = np.linspace(0, total_frames - 1, num_frames, dtype=int)
    for idx in range(total_frames):
        ok = cap.grab()  # next img
        if not ok:
            break
        if idx in frame_indices:  # only decompress needed
            ret, frame = cap.retrieve()
            if ret:
                # OpenCV uses BGR format, we need to convert it to RGB
                # for PIL and transformers compatibility
                frames.append(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))

    frames = np.stack(frames)
    if len(frames) < num_frames:
        raise ValueError(
            f"Could not read enough frames from video file {path}"
            f" (expected {num_frames} frames, got {len(frames)})"
        )
    return frames