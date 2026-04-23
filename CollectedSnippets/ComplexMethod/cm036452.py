def test_load_base64_jpeg_returns_metadata():
    """Regression test: load_base64 with video/jpeg must return metadata.

    Previously, base64 JPEG frame sequences returned an empty dict for
    metadata, which broke downstream consumers that rely on fields like
    total_num_frames and fps. See PR #37301.
    """

    num_test_frames = 3

    b64_frames = _make_jpeg_b64_frames(num_test_frames)
    data = ",".join(b64_frames)

    imageio = ImageMediaIO()
    videoio = VideoMediaIO(imageio, num_frames=num_test_frames)
    frames, metadata = videoio.load_base64("video/jpeg", data)

    # Frames array shape: (num_frames, H, W, 3)
    assert frames.shape[0] == num_test_frames

    # All required metadata keys must be present
    required_keys = {
        "total_num_frames",
        "fps",
        "duration",
        "video_backend",
        "frames_indices",
        "do_sample_frames",
    }
    assert required_keys.issubset(metadata.keys()), (
        f"Missing metadata keys: {required_keys - metadata.keys()}"
    )

    assert metadata["total_num_frames"] == num_test_frames
    assert metadata["video_backend"] == "jpeg_sequence"
    assert metadata["frames_indices"] == list(range(num_test_frames))
    assert metadata["do_sample_frames"] is False
    # Default fps=1 → duration == num_frames
    assert metadata["fps"] == 1.0
    assert metadata["duration"] == float(num_test_frames)