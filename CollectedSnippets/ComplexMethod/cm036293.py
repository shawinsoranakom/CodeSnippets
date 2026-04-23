def test_kv_cache_stride_order(monkeypatch, model_runner):
    # This test checks if GPUModelRunner initializes correctly when an attention
    # backend enforces a non-default KV cache stride order.
    n_heads = model_runner.model_config.get_num_kv_heads(model_runner.parallel_config)
    head_size = model_runner.model_config.get_head_size()

    # Get the expected shape from the backend's get_kv_cache_shape method
    # to ensure compatibility with different backends (triton vs flexattention)
    attn_backend = None
    for attn_group in model_runner._attn_group_iterator():
        attn_backend = attn_group.backend
        break

    assert attn_backend is not None, "No attention backend found"
    expected_kv_cache_shape = list(
        attn_backend.get_kv_cache_shape(NUM_BLOCKS, BLOCK_SIZE, n_heads, head_size)
    )

    # TODO mla test
    default_stride = tuple(range(5))
    # Permutation that gets you back to expected kv shape
    for test_stride in ((1, 4, 0, 2, 3), (0, 1, 2, 3, 4)):

        def rnd_stride_order(
            include_num_layers_dimension: bool = False, test_stride=test_stride
        ):
            assert not include_num_layers_dimension
            return test_stride

        # Patch the attention backend class and re-trigger the KV cache creation
        for attn_group in model_runner._attn_group_iterator():
            attn_backend = attn_group.backend
            monkeypatch.setattr(
                attn_backend, "get_kv_cache_stride_order", rnd_stride_order
            )

        model_runner.attn_groups = []
        model_runner.kv_caches = []
        model_runner.initialize_kv_cache(model_runner.kv_cache_config)

        # Shape is unchanged, but layout may differ
        kv_cache_shape = model_runner.kv_caches[0].shape
        assert list(kv_cache_shape) == expected_kv_cache_shape
        if default_stride == test_stride:
            assert all(kv.is_contiguous() for kv in model_runner.kv_caches)
        else:
            assert all(not kv.is_contiguous() for kv in model_runner.kv_caches)