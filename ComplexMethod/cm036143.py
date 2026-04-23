def test_lru_eviction_order() -> None:
    """With limited CPU space, oldest blocks should be evicted first.

    CPU block pool: num_cpu_blocks=5 -> 4 free usable blocks (1 taken by null_block).
    After storing 4 blocks (2 req_a + 2 req_b), all free slots are occupied by
    cached blocks (ref_cnt=0, in hash map).  When 2 more are stored (req_c),
    2 LRU blocks from req_a get evicted from the cache to make room.
    """
    # 5 total = 4 usable (null_block takes 1), filling exactly with 4 blocks
    fix = make_scheduler(num_cpu_blocks=5, num_gpu_blocks=16, lazy=False)
    sched = fix.scheduler

    # Fill CPU with 4 blocks: 2 requests x 2 blocks (in LRU insertion order)
    req_a = make_request(num_blocks=2)
    req_b = make_request(num_blocks=2)

    kv_a = _alloc_and_register(fix, req_a, 2)
    kv_b = _alloc_and_register(fix, req_b, 2)
    sched.update_state_after_alloc(req_a, kv_a, num_external_tokens=0)
    sched.update_state_after_alloc(req_b, kv_b, num_external_tokens=0)

    ids_a = kv_a.get_block_ids()
    ids_b = kv_b.get_block_ids()
    sched_out = make_scheduler_output(
        {
            req_a.request_id: 2 * BLOCK_SIZE,
            req_b.request_id: 2 * BLOCK_SIZE,
        },
        new_reqs={
            req_a.request_id: ids_a,
            req_b.request_id: ids_b,
        },
    )
    meta = sched.build_connector_meta(sched_out)
    assert meta.store_event >= 0
    simulate_store_completion(sched, meta.store_event)

    # Verify all 4 blocks are cached in CPU hash map
    for i, bhash in enumerate(req_a.block_hashes[:2]):
        bhash_with_group = make_block_hash_with_group_id(bhash, 0)
        assert (
            sched.cpu_block_pool.cached_block_hash_to_block.get_one_block(
                bhash_with_group
            )
            is not None
        ), f"req_a block {i} should be cached after store"
    for i, bhash in enumerate(req_b.block_hashes[:2]):
        bhash_with_group = make_block_hash_with_group_id(bhash, 0)
        assert (
            sched.cpu_block_pool.cached_block_hash_to_block.get_one_block(
                bhash_with_group
            )
            is not None
        ), f"req_b block {i} should be cached after store"

    # Store 2 more blocks from a new request - must evict 2 LRU blocks (req_a)
    req_c = make_request(num_blocks=2)
    kv_c = _alloc_and_register(fix, req_c, 2)
    sched.update_state_after_alloc(req_c, kv_c, num_external_tokens=0)

    ids_c = kv_c.get_block_ids()
    sched_out2 = make_scheduler_output(
        {req_c.request_id: 2 * BLOCK_SIZE},
        new_reqs={req_c.request_id: ids_c},
    )
    meta2 = sched.build_connector_meta(sched_out2)
    assert meta2.store_event >= 0
    simulate_store_completion(sched, meta2.store_event)

    # req_a hashes should be evicted from CPU (they were LRU)
    for i, bhash in enumerate(req_a.block_hashes[:2]):
        bhash_with_group = make_block_hash_with_group_id(bhash, 0)
        cache_map = sched.cpu_block_pool.cached_block_hash_to_block
        cached = cache_map.get_one_block(bhash_with_group)
        assert cached is None, f"req_a block {i} should have been evicted"

    # req_b and req_c hashes should be present
    for i, bhash in enumerate(req_b.block_hashes[:2]):
        bhash_with_group = make_block_hash_with_group_id(bhash, 0)
        cache_map = sched.cpu_block_pool.cached_block_hash_to_block
        cached = cache_map.get_one_block(bhash_with_group)
        assert cached is not None, f"req_b block {i} should still be cached"

    for i, bhash in enumerate(req_c.block_hashes[:2]):
        bhash_with_group = make_block_hash_with_group_id(bhash, 0)
        cache_map = sched.cpu_block_pool.cached_block_hash_to_block
        cached = cache_map.get_one_block(bhash_with_group)
        assert cached is not None, f"req_c block {i} should still be cached"