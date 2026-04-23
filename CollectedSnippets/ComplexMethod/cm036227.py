def test_computed_blocks_not_evicted():
    """
    Test that the computed blocks are not evicted when getting new blocks
    for a request if there are any other free blocks.
    """
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 3),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    # Allocate a block and cache it.
    num_tokens = block_size * 1
    req0 = make_request("0", list(range(num_tokens)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req0, num_tokens, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 1
    assert blocks.blocks[0][0].block_id == 1

    # Allocate another block.
    req1 = make_request(
        "1", list(range(num_tokens, num_tokens * 2)), block_size, sha256
    )
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req1, num_tokens, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 1
    assert blocks.blocks[0][0].block_id == 2

    # Free the blocks.
    manager.free(req0)
    manager.free(req1)

    # Now if we have a cache hit on the first block, we should evict the second
    # cached block rather than the first one.
    req2 = make_request("2", list(range(num_tokens * 2)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert len(computed_blocks.blocks[0]) == 1
    assert computed_blocks.blocks[0][0].block_id == 1
    assert num_computed_tokens == block_size

    blocks = manager.allocate_slots(
        req2,
        num_tokens * 2 - num_tokens,
        len(computed_blocks.blocks[0]) * 16,
        computed_blocks,
    )
    assert blocks is not None and len(blocks.blocks[0]) == 1
    assert blocks.blocks[0][0].block_id == 2