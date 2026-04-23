def test_pyav_backend_loads_frames(dummy_video_path, monkeypatch: pytest.MonkeyPatch):
    """Test that the pyav codec backend can load frames from a valid video."""
    with monkeypatch.context() as m:
        m.setenv("VLLM_VIDEO_LOADER_BACKEND", "opencv")

        with open(dummy_video_path, "rb") as f:
            video_data = f.read()

        loader = VIDEO_LOADER_REGISTRY.load("opencv")
        frames, metadata = loader.load_bytes(video_data, num_frames=8, backend="pyav")

        assert frames.ndim == 4
        assert frames.shape[3] == 3  # RGB
        assert frames.shape[0] == 8
        assert frames.shape[0] == len(metadata["frames_indices"])
        assert metadata["video_backend"] == "pyav"
        assert "total_num_frames" in metadata
        assert "fps" in metadata
        assert "duration" in metadata