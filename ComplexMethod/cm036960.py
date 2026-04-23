def test_generate_mm_item_video(video_dataset: RandomMultiModalDataset):
    """Test generating multimodal items for video configurations."""
    # Test video item generation
    video_config = (64, 48, 8)  # height, width, num_frames
    result = video_dataset.generate_mm_item(video_config)

    # Check the result structure matches OpenAI API format
    assert isinstance(result, dict)
    assert result["type"] == "video_url"
    assert "video_url" in result
    assert "url" in result["video_url"]

    # Check that the URL is a data URL with base64 encoded video
    url = result["video_url"]["url"]
    assert url.startswith("data:video/mp4;base64,")

    # Decode and verify the video content
    base64_data = url.split(",")[1]
    video_bytes = base64.b64decode(base64_data)
    assert len(video_bytes) > 0

    # Verify the video can be decoded
    with NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
        temp_path = temp_file.name
        temp_file.write(video_bytes)

    try:
        cap = cv2.VideoCapture(temp_path)
        assert cap.isOpened()

        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        assert frame_count == 8
        assert frame_width == 48
        assert frame_height == 64

        cap.release()
    finally:
        if os.path.exists(temp_path):
            os.unlink(temp_path)