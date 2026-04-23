def test_decode():
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
    req0 = make_request("0", common_token_ids + unique_token_ids, block_size, sha256)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req0, 55, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([1, 2, 3, 4],)

    # Append slots without allocating a new block.
    req0.num_computed_tokens = 55
    for _ in range(4):
        req0.append_output_token_ids(8)
    new_blocks = manager.allocate_slots(
        req0, 4, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert new_blocks is not None and len(new_blocks.blocks[0]) == 0
    assert (
        manager.coordinator.single_type_managers[0]
        .req_to_blocks[req0.request_id][-1]
        .block_hash
        is None
    )

    # Append slots with allocating a new block.
    req0.num_computed_tokens = 59
    # 9 tokens to fill the previous block, and 10 tokens to fill
    # the preallocated block.
    for _ in range(9 + 10):
        req0.append_output_token_ids(7)
    new_blocks = manager.allocate_slots(
        req0, 19, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert new_blocks is not None and len(new_blocks.blocks[0]) == 1
    assert (
        manager.coordinator.single_type_managers[0]
        .req_to_blocks[req0.request_id][-2]
        .block_hash
        is not None
    )
    assert (
        manager.coordinator.single_type_managers[0]
        .req_to_blocks[req0.request_id][-1]
        .block_hash
        is None
    )