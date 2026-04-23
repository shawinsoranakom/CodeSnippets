def test_prefill_not_enough_free_blocks_with_computed_blocks():
    """
    This is a unit test that tests the correctness of the allocate_slots
    when there is not enough free blocks. Specifically, when a request
    has computed blocks but cannot be allocated due to not enough free blocks,
    the computed blocks should not be touched.
    """
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config(block_size, 11),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )
    # Complete 3 blocks (48 tokens)
    # | Common-0 | Common-1 | Common-2 | ... |
    common_token_ids = [i for i in range(3) for _ in range(16)]
    req0 = make_request("0", common_token_ids, block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    manager.allocate_slots(
        req0, 48, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    block_part0 = manager.coordinator.single_type_managers[0].req_to_blocks[
        req0.request_id
    ]

    # | Common-0 | Common-1 | Common-2 | Req1-3 | Req1-4 | Req1-5 | ... |
    req1 = make_request("1", common_token_ids * 2, block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert computed_blocks.blocks[0] == block_part0
    assert num_computed_tokens == 3 * 16
    manager.allocate_slots(
        req1, 48, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    block_part1 = manager.coordinator.single_type_managers[0].req_to_blocks[
        req1.request_id
    ]
    # | Common-0 | Common-1 | Common-2 | Req1-3 (F) | Req1-4 (F) |
    # | Req1-5(F)| ... |
    manager.free(req1)
    assert {block.ref_cnt for block in block_part1[:3]} == {1}
    assert {block.ref_cnt for block in block_part1[3:]} == {0}

    # | Common-0 | Common-1 | Common-2 | Req1-3 (F) | Req1-4 (F) |
    # | Req1-5(F)| Req2-0   | Req2-1   | ... |
    req2 = make_request("2", [7] * block_size * 2, block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req2)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    manager.allocate_slots(
        req2,
        block_size * 2,
        len(computed_blocks.blocks[0]) * block_size,
        computed_blocks,
    )

    # Req3 is Req2 + 3 new blocks, so the first 6 blocks are computed,
    # but it cannot be allocated due to insufficient free blocks (2).
    # In this case, the ref_cnt of the computed blocks should not be changed.
    assert manager.block_pool.free_block_queue.num_free_blocks == 5
    req3 = make_request("3", common_token_ids * 3, block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req3)
    assert computed_blocks.blocks[0] == block_part1
    assert num_computed_tokens == 6 * 16
    # Req3 cannot be allocated.
    assert (
        manager.allocate_slots(
            req3, 48, len(computed_blocks.blocks[0]) * 16, computed_blocks
        )
        is None
    )
    # Block 0-2 are used by Req 1.
    assert {block.ref_cnt for block in block_part1[:3]} == {1}
    # Block 3-5 are free.
    assert {block.ref_cnt for block in block_part1[3:]} == {0}