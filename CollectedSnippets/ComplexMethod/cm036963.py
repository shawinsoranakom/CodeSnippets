def test_sample_mixed_buckets_with_zero_probability(
    video_dataset: RandomMultiModalDataset, hf_tokenizer: PreTrainedTokenizerBase
):
    """Test sampling with mixed buckets including zero probability entries."""
    bucket_config = {
        (64, 64, 1): 0.5,  # Images
        (64, 64, 8): 0.5,  # Videos
        (128, 128, 16): 0.0,  # Zero probability videos (should be ignored)
    }

    limit_mm_per_prompt = {"image": 2, "video": 2}

    samples = video_dataset.sample(
        tokenizer=hf_tokenizer,
        num_requests=4,
        base_items_per_request=2,
        num_mm_items_range_ratio=0.0,
        limit_mm_per_prompt=limit_mm_per_prompt,
        bucket_config=bucket_config,
        input_len=20,
        output_len=5,
    )

    assert len(samples) == 4

    # Should only see 64x64 videos, not 128x128 videos
    for sample in samples:
        mm_data = cast(list[dict[str, Any]], sample.multi_modal_data)
        for item in mm_data:
            if item["type"] == "video_url":
                # Decode video to verify dimensions
                url = item["video_url"]["url"]
                base64_data = url.split(",")[1]
                video_bytes = base64.b64decode(base64_data)

                with NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:  # noqa
                    temp_path = temp_file.name
                    temp_file.write(video_bytes)

                try:
                    cap = cv2.VideoCapture(temp_path)
                    frame_width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                    frame_height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                    cap.release()

                    # Should be 64x64, not 128x128
                    assert frame_width == 64
                    assert frame_height == 64
                finally:
                    if os.path.exists(temp_path):
                        os.unlink(temp_path)