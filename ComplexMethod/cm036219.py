def test_prefill_hybrid_model():
    block_size = 16
    manager = KVCacheManager(
        make_kv_cache_config_hybrid_model(block_size, 21, 2),
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
    )

    hash_fn = sha256

    # Complete 3 blocks (48 tokens)
    num_full_blocks = 3
    common_token_ids = [i for i in range(num_full_blocks) for _ in range(block_size)]

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
    assert blocks is not None and blocks.get_block_ids() == (
        [1, 2, 3, 4],
        [5, 6, 7, 8],
        [9, 10, 11, 12],
    )

    # Check full block metadata
    parent_block_hash = None
    for length, block_ids in zip((1, 2, 3), ((1, 5, 9), (2, 6, 10), (3, 7, 11))):
        block_tokens = tuple(all_token_ids[(length - 1) * 16 : length * 16])
        block_hash = hash_block_tokens(hash_fn, parent_block_hash, block_tokens)
        for group_id, block_id in enumerate(block_ids):
            blk_hash = manager.block_pool.blocks[block_id].block_hash
            assert blk_hash is not None
            assert get_block_hash(blk_hash) == block_hash
            assert get_group_id(blk_hash) == group_id
            assert manager.block_pool.blocks[block_id].ref_cnt == 1
        parent_block_hash = block_hash

    # Check partial block metadata
    for block_id in (4, 8, 12):
        assert manager.block_pool.blocks[block_id].block_hash is None
        assert manager.block_pool.blocks[block_id].ref_cnt == 1

    # Cache hit in the common prefix
    # Incomplete 1 block (5 tokens)
    unique_token_ids = [3] * 5
    all_token_ids = common_token_ids + unique_token_ids
    req1 = make_request("1", common_token_ids + unique_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert len(req1.block_hashes) == 3
    assert computed_blocks.get_block_ids() == ([1, 2, 3], [0, 6, 7], [0, 10, 11])
    assert num_computed_tokens == 3 * 16
    num_new_tokens = 53 - 3 * 16
    blocks = manager.allocate_slots(
        req1, num_new_tokens, len(computed_blocks.blocks[0]) * 16, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == ([13], [14], [15])
    for block_per_group in computed_blocks.blocks:
        for block in block_per_group:
            if block != manager.block_pool.null_block:
                assert block.ref_cnt == 2

    block_hashes = req1.block_hashes
    manager.free(req0)
    manager.free(req1)

    # Evict the blocks outside sliding window, does not affect the hit length.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "2",
        all_token_ids,
        [
            make_block_hash_with_group_id(block_hashes[0], 1),
            make_block_hash_with_group_id(block_hashes[0], 2),
        ],
        3,
    )

    # Evict the first block of full attention, makes total cache miss.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "3",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[0], 0)],
        0,
    )

    # Evict the last block of all layers, reduces the hit length to 2.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "4",
        all_token_ids,
        [
            make_block_hash_with_group_id(block_hashes[2], 0),
            make_block_hash_with_group_id(block_hashes[2], 1),
            make_block_hash_with_group_id(block_hashes[2], 2),
        ],
        2,
    )

    # Evict the last block of full attention, reduces the hit length to 2.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "5",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[2], 0)],
        2,
    )

    # Evict the last block of sliding window, reduces the hit length to 2.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "6",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[2], 1)],
        2,
    )

    # Evict the last block of sliding window, reduces the hit length to 2.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "7",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[2], 2)],
        2,
    )

    # Evict different set of blocks for full attention and sliding window makes
    # total cache miss.
    # The cache hit length of full attention is 1 * block_size.
    # The cache hit length of sliding window is 2 * block_size.
    # Then it is cache miss as the two type of layers
    # have different hit length.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "8",
        all_token_ids,
        [
            make_block_hash_with_group_id(block_hashes[2], 0),
            make_block_hash_with_group_id(block_hashes[0], 1),
            make_block_hash_with_group_id(block_hashes[0], 2),
        ],
        0,
    )