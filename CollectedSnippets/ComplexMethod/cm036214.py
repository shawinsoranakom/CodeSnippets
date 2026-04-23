def test_merge_kv_cache_spec():
    same_layer_specs = [
        new_kv_cache_spec(num_kv_heads=32),
        new_kv_cache_spec(num_kv_heads=32),
    ]
    merged_layer_spec = same_layer_specs[0].merge(same_layer_specs)
    assert merged_layer_spec.block_size == 16
    assert merged_layer_spec.num_kv_heads == 32
    assert merged_layer_spec.head_size == 64
    assert merged_layer_spec.dtype == torch.float32
    assert merged_layer_spec.sliding_window is None

    different_layer_specs = [
        new_kv_cache_spec(num_kv_heads=32),
        new_kv_cache_spec(num_kv_heads=16),
    ]
    with pytest.raises(AssertionError):
        different_layer_specs[0].merge(different_layer_specs)

    full_spec = new_kv_cache_spec(num_kv_heads=32)
    different_type_layer_specs = [
        full_spec,
        SlidingWindowSpec(
            block_size=full_spec.block_size,
            num_kv_heads=full_spec.num_kv_heads,
            head_size=full_spec.head_size,
            dtype=full_spec.dtype,
            sliding_window=1,
        ),
    ]
    with pytest.raises(AssertionError):
        different_type_layer_specs[0].merge(different_type_layer_specs)
    with pytest.raises(AssertionError):
        different_type_layer_specs[1].merge(different_type_layer_specs)

    different_sliding_window_layer_specs = [
        new_kv_cache_spec(num_kv_heads=32),
        new_kv_cache_spec(num_kv_heads=32, sliding_window=1),
        new_kv_cache_spec(num_kv_heads=32, sliding_window=2),
    ]
    with pytest.raises(ValueError):
        different_sliding_window_layer_specs[0].merge(
            different_sliding_window_layer_specs
        )

    same_sliding_window_layer_specs = [
        new_kv_cache_spec(num_kv_heads=32, sliding_window=1),
        new_kv_cache_spec(num_kv_heads=32, sliding_window=1),
    ]
    merged_layer_spec = same_sliding_window_layer_specs[0].merge(
        same_sliding_window_layer_specs
    )
    assert merged_layer_spec.sliding_window == 1

    same_sliding_window_layer_spec_with_none = [
        new_kv_cache_spec(num_kv_heads=32, sliding_window=1),
        new_kv_cache_spec(num_kv_heads=32, sliding_window=None),
    ]
    merged_layer_spec = same_sliding_window_layer_spec_with_none[0].merge(
        same_sliding_window_layer_spec_with_none
    )
    assert merged_layer_spec.sliding_window == 1