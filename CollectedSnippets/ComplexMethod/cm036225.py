def test_evict():
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 11),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    last_token_id = 5 * 16 + 7
    req0 = make_request("0", list(range(last_token_id)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req0, 5 * 16 + 7, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    # 5 full + 1 partial
    assert blocks is not None and len(blocks.blocks[0]) == 6

    # 3 blocks.
    req1 = make_request(
        "1", list(range(last_token_id, last_token_id + 3 * 16)), block_size, sha256
    )
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req1, 3 * 16, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and len(blocks.blocks[0]) == 3  # 3 full blocks
    last_token_id += 3 * 16

    # 10 - (6 + 3) == 1
    assert manager.block_pool.free_block_queue.num_free_blocks == 1

    manager.free(req0)
    manager.free(req1)
    assert manager.block_pool.free_block_queue.num_free_blocks == 10
    assert [
        b.block_id for b in manager.block_pool.free_block_queue.get_all_free_blocks()
    ] == [10, 6, 5, 4, 3, 2, 1, 9, 8, 7]

    # Touch the first 2 blocks.
    req2 = make_request("2", list(range(2 * 16 + 3)), block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert computed_blocks.get_block_ids() == ([1, 2],)
    assert num_computed_tokens == 2 * 16
    blocks = manager.allocate_slots(
        req2, 3, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([10],)
    assert manager.block_pool.free_block_queue.num_free_blocks == 7