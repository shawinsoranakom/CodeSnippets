def test_sample_video_only_buckets(
    video_dataset: RandomMultiModalDataset, hf_tokenizer: PreTrainedTokenizerBase
):
    """Test sampling with only video buckets."""
    bucket_config = {
        (64, 64, 8): 1.0,  # Only videos
    }

    limit_mm_per_prompt = {"image": 0, "video": 2}

    samples = video_dataset.sample(
        tokenizer=hf_tokenizer,
        num_requests=3,
        base_items_per_request=1,
        num_mm_items_range_ratio=0.0,
        limit_mm_per_prompt=limit_mm_per_prompt,
        bucket_config=bucket_config,
        input_len=20,
        output_len=5,
    )

    assert len(samples) == 3

    for sample in samples:
        assert isinstance(sample, SampleRequest)
        assert sample.multi_modal_data is not None
        assert isinstance(sample.multi_modal_data, list)

        mm_data = cast(list[dict[str, Any]], sample.multi_modal_data)
        assert len(mm_data) == 1

        item = mm_data[0]
        assert item["type"] == "video_url"
        url = item["video_url"]["url"]
        assert url.startswith("data:video/mp4;base64,")