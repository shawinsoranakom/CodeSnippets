def test_random_mm_bucket_config_not_mutated(
    hf_tokenizer: PreTrainedTokenizerBase,
) -> None:
    ds = RandomMultiModalDataset(random_seed=0)
    # This bucket config is not normalized to sum to 1
    # and has more buckets than requested images
    original = {(32, 32, 1): 0.2, (52, 64, 1): 6, (25, 64, 1): 3}
    # Keep a snapshot to compare after sampling
    snapshot = dict(original)

    _ = _collect_mm_samples(
        ds,
        hf_tokenizer,
        num_requests=4,
        base_items_per_request=1,
        num_mm_items_range_ratio=0.0,
        limit_mm_per_prompt={"image": 1, "video": 0},
        bucket_config=original,
    )

    # Ensure the original dict content is unchanged
    assert original == snapshot

    # Vary number of mm items per prompt
    # set num_mm_items_range_ratio to 0.5
    samples_varying_items = _collect_mm_samples(
        ds,
        hf_tokenizer,
        num_requests=5,
        base_items_per_request=2,
        num_mm_items_range_ratio=0.5,
        limit_mm_per_prompt={"image": 4, "video": 0},
        bucket_config={(32, 32, 1): 1.0},
    )
    # Must have 5 requests each with less than 4 mm items per prompt
    # but at least 1 mm item per prompt
    assert len(samples_varying_items) == 5
    for s in samples_varying_items:
        mm_data = cast(list[dict[str, Any]], s.multi_modal_data)
        assert len(mm_data) <= 4
        assert len(mm_data) >= 1
        for it in mm_data:
            assert it.get("type") == "image_url"