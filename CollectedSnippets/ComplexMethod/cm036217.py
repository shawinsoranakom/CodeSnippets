def test_unify_hybrid_kv_cache_specs():
    # 1. has_full_attention and has_sliding_window
    before_spec_1 = new_kv_cache_spec()
    before_spec_2 = new_sliding_window_spec(
        page_size_padded=32 * 1024, sliding_window=1024
    )
    kv_cache_spec = {
        "layer_1": before_spec_1,
        "layer_2": before_spec_2,
    }
    kv_cache_utils.unify_hybrid_kv_cache_specs(kv_cache_spec)
    expected_spec_1 = new_kv_cache_spec()
    expected_spec_2 = new_kv_cache_spec(page_size_padded=32 * 1024, sliding_window=1024)
    assert kv_cache_spec["layer_1"] == expected_spec_1
    assert kv_cache_spec["layer_2"] == expected_spec_2

    # 2. has_full_attention and has_chunked_local_attention
    before_spec_1 = new_kv_cache_spec()
    before_spec_2 = new_chunked_local_attention_spec(
        page_size_padded=32 * 1024, attention_chunk_size=512
    )
    kv_cache_spec = {
        "layer_1": before_spec_1,
        "layer_2": before_spec_2,
    }
    kv_cache_utils.unify_hybrid_kv_cache_specs(kv_cache_spec)
    expected_spec_1 = new_kv_cache_spec()
    expected_spec_2 = new_kv_cache_spec(
        page_size_padded=32 * 1024, attention_chunk_size=512
    )

    assert kv_cache_spec["layer_1"] == expected_spec_1
    assert kv_cache_spec["layer_2"] == expected_spec_2

    # 3. has_full_attention, has_sliding_window and has_chunked_local_attention
    before_spec_1 = new_kv_cache_spec()
    before_spec_2 = new_sliding_window_spec(
        page_size_padded=32 * 1024, sliding_window=1024
    )
    before_spec_3 = new_chunked_local_attention_spec(
        page_size_padded=32 * 1024, attention_chunk_size=512
    )
    kv_cache_spec = {
        "layer_1": before_spec_1,
        "layer_2": before_spec_2,
        "layer_3": before_spec_3,
    }
    kv_cache_utils.unify_hybrid_kv_cache_specs(kv_cache_spec)
    expected_spec_1 = new_kv_cache_spec()
    expected_spec_2 = new_kv_cache_spec(page_size_padded=32 * 1024, sliding_window=1024)
    expected_spec_3 = new_kv_cache_spec(
        page_size_padded=32 * 1024, attention_chunk_size=512
    )
    assert kv_cache_spec["layer_1"] == expected_spec_1
    assert kv_cache_spec["layer_2"] == expected_spec_2
    assert kv_cache_spec["layer_3"] == expected_spec_3

    # 4. No FullAttentionSpec, should not convert
    kv_cache_spec = {
        "layer_1": new_sliding_window_spec(sliding_window=1024),
        "layer_2": new_chunked_local_attention_spec(attention_chunk_size=512),
    }

    with pytest.raises(ValueError):
        kv_cache_utils.unify_hybrid_kv_cache_specs(kv_cache_spec)