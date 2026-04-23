def test_random_mm_video_sampling(hf_tokenizer: PreTrainedTokenizerBase) -> None:
    """Test video sampling functionality in RandomMultiModalDataset."""
    ds = RandomMultiModalDataset(random_seed=42)

    # Test with video bucket configuration
    bucket_config = {
        (64, 64, 1): 0.3,  # Images
        (64, 64, 8): 0.7,  # Videos
    }

    limit_mm_per_prompt = {"image": 2, "video": 2}

    samples = _collect_mm_samples(
        ds,
        hf_tokenizer,
        num_requests=5,
        base_items_per_request=1,
        num_mm_items_range_ratio=0.0,
        limit_mm_per_prompt=limit_mm_per_prompt,
        bucket_config=bucket_config,
    )

    assert len(samples) == 5

    # Check that we have both images and videos
    video_count = 0
    image_count = 0

    for s in samples:
        mm_data = cast(list[dict[str, Any]], s.multi_modal_data)
        assert len(mm_data) == 1

        item = mm_data[0]
        if item.get("type") == "video_url":
            video_count += 1
            # Verify video URL format
            url = item.get("video_url", {}).get("url", "")
            assert url.startswith("data:video/mp4;base64,")
        elif item.get("type") == "image_url":
            image_count += 1
            # Verify image URL format
            url = item.get("image_url", {}).get("url", "")
            assert url.startswith("data:image/jpeg;base64,")

    # Should have some videos due to 0.7 probability
    assert video_count > 0
    assert image_count > 0