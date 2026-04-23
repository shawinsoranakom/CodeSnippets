def test_prefill(hash_fn):
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 11),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    # Complete 3 blocks (48 tokens)
    common_token_ids = [i for i in range(3) for _ in range(16)]

    # Fully cache miss
    # Incomplete 1 block (7 tokens)
    unique_token_ids = [3] * 7
    all_token_ids = common_token_ids + unique_token_ids
    req0 = make_request("0", all_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert len(req0.block_hashes) == 3
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req0, 55, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([1, 2, 3, 4],)

    # Check full block metadata
    parent_block_hash = None
    for block_id in (1, 2, 3):
        block_tokens = tuple(all_token_ids[(block_id - 1) * 16 : block_id * 16])
        block_hash = hash_block_tokens(hash_fn, parent_block_hash, block_tokens)
        blk_hash = manager.block_pool.blocks[block_id].block_hash
        assert blk_hash is not None
        assert get_block_hash(blk_hash) == block_hash
        assert get_group_id(blk_hash) == 0
        assert manager.block_pool.blocks[block_id].ref_cnt == 1
        parent_block_hash = block_hash

    # Check partial block metadata
    for block_id in (4,):
        assert manager.block_pool.blocks[block_id].block_hash is None
        assert manager.block_pool.blocks[block_id].ref_cnt == 1

    # Cache hit in the common prefix when the original block is still in use.
    # Incomplete 1 block (5 tokens)
    unique_token_ids = [3] * 5
    req1 = make_request("1", common_token_ids + unique_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert len(req1.block_hashes) == 3
    assert computed_blocks.get_block_ids() == ([1, 2, 3],)
    assert num_computed_tokens == 3 * 16
    num_new_tokens = 53 - 3 * 16
    blocks = manager.allocate_slots(
        req1, num_new_tokens, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([5],)
    for block in computed_blocks.blocks[0]:
        assert block.ref_cnt == 2

    # At this point, we should have 5 free blocks left.
    free_block_queue = manager.block_pool.free_block_queue
    assert free_block_queue.num_free_blocks == 5

    manager.free(req0)
    manager.free(req1)

    # All blocks should be available.
    assert free_block_queue.num_free_blocks == 10
    # The order should be
    # [unallocated (6, 7, 8, 9, 10)]
    # [unique_req0 (4)]
    # [unique_req1 (5)]
    # [common (3, 2, 1)]
    assert [
        b.block_id for b in manager.block_pool.free_block_queue.get_all_free_blocks()
    ] == [6, 7, 8, 9, 10, 4, 5, 3, 2, 1]

    # Cache hit in the common prefix when the original block is already free.
    # Incomplete 1 block (6 tokens)
    unique_token_ids = [3] * 6
    req2 = make_request("2", common_token_ids + unique_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert len(req2.block_hashes) == 3
    assert computed_blocks.get_block_ids() == ([1, 2, 3],)
    assert num_computed_tokens == 3 * 16
    num_new_tokens = 53 - 3 * 16
    blocks = manager.allocate_slots(
        req2, num_new_tokens, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([6],)

    # Although we only have 6 free blocks, we have 8 blocks in
    # the free block queue due to lazy removal.
    assert free_block_queue.num_free_blocks == 6
    assert all([b.ref_cnt == 0 for b in free_block_queue.get_all_free_blocks()])
    assert len([b for b in free_block_queue.get_all_free_blocks()]) == 6

    manager.free(req2)

    # Cache miss and eviction.
    req3 = make_request("3", [99] * (16 * 10), block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req3)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req3, 16 * 10, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    # This block ID order also checks the eviction order.
    assert blocks is not None and blocks.get_block_ids() == (
        [7, 8, 9, 10, 4, 5, 6, 3, 2, 1],
    )

    assert free_block_queue.num_free_blocks == 0
    assert (
        free_block_queue.fake_free_list_head.next_free_block
        is free_block_queue.fake_free_list_tail
    )
    assert (
        free_block_queue.fake_free_list_tail.prev_free_block
        is free_block_queue.fake_free_list_head
    )