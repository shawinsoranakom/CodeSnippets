def test_prefill_hybrid_model_eagle():
    block_size = 16
    kv_cache_config = make_kv_cache_config_hybrid_model(block_size, 31, 3)
    manager = KVCacheManager(
        kv_cache_config,
        max_model_len=8192,
        enable_caching=True,
        hash_block_size=block_size,
        use_eagle=True,
    )

    hash_fn = sha256

    # Complete 6 blocks (96 tokens)
    num_full_blocks = 6
    common_token_ids = [i for i in range(num_full_blocks) for _ in range(block_size)]

    # Fully cache miss
    # Incomplete 1 block (7 tokens)
    unique_token_ids = [6] * 7
    all_token_ids = common_token_ids + unique_token_ids
    req0 = make_request("0", all_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req0)
    assert len(req0.block_hashes) == len(all_token_ids) // block_size
    assert not computed_blocks.blocks[0]
    assert num_computed_tokens == 0
    blocks = manager.allocate_slots(
        req0, len(all_token_ids), num_computed_tokens, computed_blocks
    )
    block_ids = (
        [1, 2, 3, 4, 5, 6, 7],
        [8, 9, 10, 11, 12, 13, 14],
        [15, 16, 17, 18, 19, 20, 21],
    )
    assert blocks is not None and blocks.get_block_ids() == block_ids

    # Check full block metadata
    parent_block_hash = None
    for i, full_block_ids in enumerate(zip(*(row[:-1] for row in block_ids))):
        block_tokens = tuple(all_token_ids[i * block_size : (i + 1) * block_size])
        block_hash = hash_block_tokens(hash_fn, parent_block_hash, block_tokens)
        for group_id, block_id in enumerate(full_block_ids):
            blk_hash = manager.block_pool.blocks[block_id].block_hash
            assert blk_hash is not None
            assert get_block_hash(blk_hash) == block_hash
            assert get_group_id(blk_hash) == group_id
            assert manager.block_pool.blocks[block_id].ref_cnt == 1
        parent_block_hash = block_hash

    # Check partial block metadata
    for partial_block_id in (row[-1] for row in block_ids):
        assert manager.block_pool.blocks[partial_block_id].block_hash is None
        assert manager.block_pool.blocks[partial_block_id].ref_cnt == 1

    # Cache hit in the common prefix
    # Incomplete 1 block (5 tokens)
    unique_token_ids = [6] * 5
    all_token_ids = common_token_ids + unique_token_ids
    req1 = make_request("1", all_token_ids, block_size, hash_fn)
    computed_blocks, num_computed_tokens = manager.get_computed_blocks(req1)
    assert len(req1.block_hashes) == num_full_blocks
    assert computed_blocks.get_block_ids() == (
        [1, 2, 3, 4],
        [0, 9, 10, 11],
        [0, 16, 17, 18],
    )
    assert num_computed_tokens == 4 * block_size
    num_new_tokens = len(all_token_ids) - num_computed_tokens
    blocks = manager.allocate_slots(
        req1, num_new_tokens, num_computed_tokens, computed_blocks
    )
    assert blocks is not None and blocks.get_block_ids() == (
        [22, 23, 24],
        [25, 26, 27],
        [28, 29, 30],
    )
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
        4,
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

    # Evict the last block of all layers, reduces the hit length to 3.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "4",
        all_token_ids,
        [
            make_block_hash_with_group_id(block_hashes[-1], 0),
            make_block_hash_with_group_id(block_hashes[-1], 1),
            make_block_hash_with_group_id(block_hashes[-1], 2),
        ],
        3,
    )

    # Evict the last block of full attention, reduces the hit length to 3.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "5",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[-1], 0)],
        3,
    )

    # Since the last block of full attention is dropped for eagle, evict
    # the second last block of sliding window, reduces the hit length to 3.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "6",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[-2], 1)],
        3,
    )

    # Since the last block of full attention is dropped for eagle, evict
    # the second last block of sliding window, reduces the hit length to 3.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "7",
        all_token_ids,
        [make_block_hash_with_group_id(block_hashes[-2], 2)],
        3,
    )

    # Evict different set of blocks for full attention and sliding window makes
    # total cache miss.
    # The cache hit length of full attention is 4 * block_size.
    # The cache hit length of sliding window is 3 * block_size.
    # Then it is cache miss as the two type of layers
    # have different hit length.
    _test_partial_request_hit(
        manager,
        block_size,
        num_full_blocks,
        "8",
        all_token_ids,
        [
            make_block_hash_with_group_id(block_hashes[-1], 0),
            make_block_hash_with_group_id(block_hashes[0], 1),
            make_block_hash_with_group_id(block_hashes[0], 2),
        ],
        0,
    )