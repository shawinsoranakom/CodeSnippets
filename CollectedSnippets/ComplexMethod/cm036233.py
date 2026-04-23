def test_reset_prefix_cache():
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 11),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    full_block_token_ids = [i for i in range(3) for _ in range(16)]
    unique_token_ids = [3] * 7
    all_token_ids = full_block_token_ids + unique_token_ids
    req0 = make_request("0", all_token_ids, block_size, sha256)
    blocks = manager.allocate_slots(req0, 55)
    assert blocks is not None and blocks.get_block_ids() == ([1, 2, 3, 4],)

    unique_token_ids = [4] * 7
    all_token_ids = full_block_token_ids + unique_token_ids
    req1 = make_request("1", all_token_ids, block_size, sha256)
    computed_blocks, _ = manager.get_computed_blocks(req1)
    assert len(req1.block_hashes) == 3
    assert len(computed_blocks.blocks[0]) == 3
    blocks = manager.allocate_slots(
        req1, 7, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([5],)

    # Failed to reset prefix cache because some blocks are not freed yet.
    assert not manager.reset_prefix_cache()
    assert manager.block_pool.cached_block_hash_to_block

    # Free the blocks.
    manager.free(req0)
    manager.free(req1)

    assert manager.reset_prefix_cache()
    assert not manager.block_pool.cached_block_hash_to_block
    assert all([blk.block_hash is None for blk in manager.block_pool.blocks])