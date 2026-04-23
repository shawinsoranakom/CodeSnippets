def test_multi_group_null_blocks_skipped() -> None:
    """Null GPU blocks (no block_hash) must not appear in store or load pairs.

    In eager store mode, _prepare_eager_store_specs skips blocks whose
    block_hash is None (null blocks have no hash). We verify this by mixing
    real hashed blocks with unhashed (null-like) blocks in a single group and
    checking that only real blocks appear in the store list.
    """
    fix = make_scheduler(num_cpu_blocks=8, num_gpu_blocks=16, num_groups=1, lazy=False)
    sched = fix.scheduler
    gpu_pool = fix.gpu_block_pool

    num_blocks = 2
    req = make_request(num_blocks=num_blocks)

    # Allocate real blocks (with hashes) and use the null_block as a placeholder
    gpu_blocks = _allocate_gpu_blocks(gpu_pool, req, num_blocks, group_id=0)
    null_block = gpu_pool.null_block

    # Mix: [real_block, null_block] — null_block has no hash, should be skipped
    mixed_blocks = [gpu_blocks[0], null_block]
    kv_blocks = KVCacheBlocks(blocks=(mixed_blocks,))
    req.num_computed_tokens = num_blocks * BLOCK_SIZE
    sched.update_state_after_alloc(req, kv_blocks, num_external_tokens=0)

    block_ids = kv_blocks.get_block_ids()
    sched_out = make_scheduler_output(
        {req.request_id: num_blocks * BLOCK_SIZE},
        new_reqs={req.request_id: block_ids},
    )
    meta = sched.build_connector_meta(sched_out)

    # Null block's ID should NOT appear in store_gpu_blocks
    null_block_id = null_block.block_id
    assert null_block_id not in meta.store_gpu_blocks, (
        f"Null block id {null_block_id} should not appear in store transfer pairs"
    )

    # Only real block should be scheduled for store
    assert len(meta.store_gpu_blocks) == 1
    assert gpu_blocks[0].block_id in meta.store_gpu_blocks

    # Complete the store
    assert meta.store_event >= 0
    simulate_store_completion(sched, meta.store_event)

    # Create matching request and get load hit
    req2 = Request(
        request_id="req-null-load",
        prompt_token_ids=req.prompt_token_ids,
        sampling_params=req.sampling_params,
        pooling_params=None,
        mm_features=None,
        block_hasher=req._block_hasher,
    )
    hit_tokens, is_async = sched.get_num_new_matched_tokens(req2, num_computed_tokens=0)
    # Only 1 block was stored (the real one)
    assert hit_tokens == BLOCK_SIZE
    assert is_async is True

    # Allocate new GPU blocks for the load
    gpu_blocks2 = gpu_pool.get_new_blocks(1)
    kv_blocks2 = KVCacheBlocks(blocks=([gpu_blocks2[0], null_block],))
    sched.update_state_after_alloc(req2, kv_blocks2, num_external_tokens=hit_tokens)

    sched_out2 = make_scheduler_output({req2.request_id: 1})
    meta2 = sched.build_connector_meta(sched_out2)

    # Null block's ID should NOT appear in load_gpu_blocks
    assert null_block_id not in meta2.load_gpu_blocks, (
        f"Null block id {null_block_id} should not appear in load transfer pairs"
    )