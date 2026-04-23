def test_prefill_hybrid_model_combinations(spec_types: list[str]):
    """
    Test prefix caching with hybrid models containing various combinations of
    KV cache spec types.

    This unified test covers:
    - Various combinations (full attn + other attn types)
    - Varying number of groups (2, 3, or 4)
    - 0, 1, or 2 full attention groups in the combination
    - Two sliding_window attn groups with different window sizes
    - Interleaved group IDs (full attn and other types alternating)
    - Mamba spec with other attention types
    """
    block_size = 16
    num_groups = len(spec_types)
    # Allocate enough blocks for all groups
    num_blocks = 10 * num_groups

    kv_cache_config = _make_hybrid_kv_cache_config(block_size, num_blocks, spec_types)
    manager = KVCacheManager(
        kv_cache_config,
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    hash_fn = sha256

    # Complete 3 blocks (48 tokens)
    common_token_ids = [i for i in range(3) for _ in range(block_size)]
    unique_token_ids = [3] * 7
    all_token_ids = common_token_ids + unique_token_ids

    # First request: no cache hit initially
    req0 = make_request("0", all_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)

    assert len(req0.block_hashes) == 3
    assert not computed_blocks.blocks[0]  # No cache hit initially
    assert num_computed_tokens == 0

    blocks = manager.allocate_slots(
        req0, 55, len(computed_blocks.blocks[0]) * block_size, computed_blocks
    )
    assert blocks is not None
    # Should have blocks for all groups
    assert len(blocks.get_block_ids()) == num_groups

    manager.new_step_starts()

    # Second request: should hit cached blocks for common prefix
    req1 = make_request("1", common_token_ids + [4] * 5, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)

    # Should hit cached blocks for all groups
    assert num_computed_tokens == 3 * block_size
    assert len(computed_blocks.blocks) == num_groups

    # Allocate and verify blocks for second request
    blocks = manager.allocate_slots(
        req1,
        len(common_token_ids) + 5 - num_computed_tokens,
        num_computed_tokens,
        computed_blocks,
    )
    assert blocks is not None
    assert len(blocks.get_block_ids()) == num_groups

    manager.free(req0)
    manager.free(req1)