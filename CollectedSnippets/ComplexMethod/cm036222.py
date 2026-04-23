def test_prefill_hybrid_model_combinations_eagle(
    spec_types: list[str], expect_hit_length: int
):
    """
    Test prefix caching with hybrid models (1 full attn + 1 other) with EAGLE.
    More complex hybrid models with EAGLE are not yet supported (see issue #32802).
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
        use_eagle=True,
    )

    hash_fn = sha256

    # Complete 3 blocks (48 tokens)
    num_full_blocks = 4
    common_token_ids = [i for i in range(num_full_blocks) for _ in range(block_size)]
    unique_token_ids = [4] * 7
    all_token_ids = common_token_ids + unique_token_ids

    # First request: no cache hit initially
    req0 = make_request("0", all_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)

    assert len(req0.block_hashes) == num_full_blocks
    assert not computed_blocks.blocks[0]  # No cache hit initially
    assert num_computed_tokens == 0

    blocks = manager.allocate_slots(
        req0, len(all_token_ids), num_computed_tokens, computed_blocks
    )
    assert blocks is not None
    # Should have blocks for all groups
    assert len(blocks.get_block_ids()) == num_groups

    # Second request: should hit cached blocks for common prefix
    all_token_ids = common_token_ids + [6] * 5
    req1 = make_request("1", all_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)

    # Should hit cached blocks for all groups
    assert num_computed_tokens == expect_hit_length * block_size
    assert len(computed_blocks.blocks) == num_groups
    # Verify each group has the correct number of computed blocks
    for block_per_group in computed_blocks.blocks:
        assert len(block_per_group) == expect_hit_length

    # Allocate and verify blocks for second request
    blocks = manager.allocate_slots(
        req1,
        len(all_token_ids) - num_computed_tokens,
        num_computed_tokens,
        computed_blocks,
    )
    assert blocks is not None
    assert len(blocks.get_block_ids()) == num_groups

    manager.free(req0)
    manager.free(req1)