def test_basic_prefix_caching_disabled():
    """
    This tests that the prefix caching is disabled.
    """
    block_size = 4
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 5),
        max_model_len=8192,
        enable_caching=False,
        hash_block_size=block_size,
    )

    req1 = make_request(
        "1", list(range(10)), block_size, sha256
    )  # 2 blocks and some more

    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req1, 10, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 3

    # Free the blocks.
    manager.free(req1)

    # No caching.
    req2 = make_request("2", list(range(16)), block_size, sha256)  # shared prefix
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req2, 16, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 4

    # New requests should not have any blocks.
    req3 = make_request("3", list(range(4)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req3)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req3, 4, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert not blocks