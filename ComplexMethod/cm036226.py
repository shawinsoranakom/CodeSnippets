def test_hash_block_correct_reuse():
    """
    This tests when a previously cached block is reused as a new block,
    its hash metadata should be correctly reset.
    """
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(16, 2),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    # Allocate 1 block and cache it.
    num_tokens = block_size * 1
    req = make_request("0", list(range(num_tokens)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req, num_tokens, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 1

    # Deallocate the block.
    manager.free(req)

    # Allocate a new block that's not full, make sure hash info on the
    # block is cleared.
    req = make_request("1", list(range(num_tokens - 1)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req, num_tokens - 1, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 1

    assert manager.block_pool.blocks[blocks.blocks[0][0].block_id].block_hash is None