def test_sample_with_video_buckets(
    video_dataset: RandomMultiModalDataset, hf_tokenizer: PreTrainedTokenizerBase
):
    """Test sampling with video bucket configurations."""
    # Configure bucket with video probability > 0
    bucket_config = {
        (64, 64, 1): 0.3,  # Images
        (64, 64, 8): 0.7,  # Videos
    }

    limit_mm_per_prompt = {"image": 5, "video": 3}

    samples = video_dataset.sample(
        tokenizer=hf_tokenizer,
        num_requests=5,
        base_items_per_request=2,
        num_mm_items_range_ratio=0.0,
        limit_mm_per_prompt=limit_mm_per_prompt,
        bucket_config=bucket_config,
        input_len=20,
        output_len=5,
    )

    assert len(samples) == 5

    # Check that samples contain both images and videos
    video_count = 0
    image_count = 0

    for sample in samples:
        assert isinstance(sample, SampleRequest)
        assert sample.multi_modal_data is not None
        assert isinstance(sample.multi_modal_data, list)

        mm_data = cast(list[dict[str, Any]], sample.multi_modal_data)
        assert len(mm_data) == 2  # base_items_per_request

        for item in mm_data:
            if item["type"] == "video_url":
                video_count += 1
                # Verify video URL format
                url = item["video_url"]["url"]
                assert url.startswith("data:video/mp4;base64,")
            elif item["type"] == "image_url":
                image_count += 1
                # Verify image URL format
                url = item["image_url"]["url"]
                assert url.startswith("data:image/jpeg;base64,")

    # Should have some videos due to 0.7 probability
    assert video_count > 0
    assert image_count > 0