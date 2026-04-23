def test_null_parent_block_hash():
    block_size = 1
    num_cached_blocks = 2
    num_full_blocks = 4
    kv_cache_group_id = 0

    pool = BlockPool(
        num_gpu_blocks=8,
        enable_caching=True,
        hash_block_size=block_size,
        enable_kv_cache_events=True,
    )

    req = make_request(
        "req_null_parent",
        prompt_token_ids=[10, 11, 12, 13],
        block_size=block_size,
        hash_fn=sha256,
    )
    assert len(req.block_hashes) == num_full_blocks

    # Physical parent is `null_block` (no hash), while the logical parent hash
    # still exists in `request.block_hashes[num_cached_blocks - 1]`.
    assert pool.null_block.block_hash is None
    new_blocks = pool.get_new_blocks(num_full_blocks - 1)
    blocks = [
        new_blocks[: num_cached_blocks - 1],
        pool.null_block,  # physical parent
        *new_blocks[num_cached_blocks - 1 :],
    ]

    pool.cache_full_blocks(
        request=req,
        blocks=blocks,
        num_cached_blocks=num_cached_blocks,
        num_full_blocks=num_full_blocks,
        block_size=block_size,
        kv_cache_group_id=kv_cache_group_id,
    )

    events = pool.take_events()
    assert len(events) == 1
    event = events[0]
    assert isinstance(event, BlockStored)

    expected_parent = kv_cache_utils.maybe_convert_block_hash(
        req.block_hashes[num_cached_blocks - 1]
    )
    assert event.parent_block_hash == expected_parent
    assert event.parent_block_hash is not None

    expected_new_hashes = [
        kv_cache_utils.maybe_convert_block_hash(h)
        for h in req.block_hashes[num_cached_blocks:num_full_blocks]
    ]
    assert event.block_hashes == expected_new_hashes
    assert event.group_idx == kv_cache_group_id

    # Ensure we didn't accidentally assign a hash to the null block.
    assert pool.null_block.block_hash is None
    # Sanity check: newly cached physical blocks should have hashes assigned.
    assert blocks[num_cached_blocks].block_hash is not None
    assert blocks[num_full_blocks - 1].block_hash is not None