def test_partial_gpu_prefix_plus_cpu_load() -> None:
    """When GPU has a prefix cache hit for the first N blocks, CPU has a
    hit for the next M blocks, and there are P new blocks needing fresh
    compute, the block layout is:

        | comp (N) | ext_comp (M) | new (P) |

    External blocks sit in the middle — not at the beginning or end.
    The load path must target hashes at positions [N, N+M).

    Request: 6 blocks (0..5).
    - Store all 6 to CPU.
    - New request: GPU prefix cache hits blocks 0,1 (hashed).
      CPU hits blocks 2,3. Blocks 4,5 are new (need compute).
    - update_state_after_alloc receives 6 GPU blocks:
      [0,1] hashed (comp), [2,3] unhashed (ext_comp), [4,5] unhashed (new).
    - Load must target hash positions 2,3.
    """
    fix = make_scheduler(num_cpu_blocks=8, num_gpu_blocks=16, lazy=False)
    sched = fix.scheduler
    gpu_pool = fix.gpu_block_pool

    num_blocks = 6
    req = make_request(num_blocks=num_blocks)

    # Store all 6 blocks to CPU via eager store.
    kv_blocks = _alloc_and_register(fix, req, num_blocks)
    sched.update_state_after_alloc(req, kv_blocks, num_external_tokens=0)
    block_ids = kv_blocks.get_block_ids()
    sched_out = make_scheduler_output(
        {req.request_id: num_blocks * BLOCK_SIZE},
        new_reqs={req.request_id: block_ids},
    )
    meta = sched.build_connector_meta(sched_out)
    assert meta.store_event >= 0
    simulate_store_completion(sched, meta.store_event)

    # New request with same tokens — but only partial GPU prefix hit.
    req2 = Request(
        request_id="req-partial-gpu",
        prompt_token_ids=req.prompt_token_ids,
        sampling_params=req.sampling_params,
        pooling_params=None,
        mm_features=None,
        block_hasher=req._block_hasher,
    )

    # GPU prefix cache hits the first 2 blocks.
    gpu_local_computed = 2 * BLOCK_SIZE
    hit_tokens, is_async = sched.get_num_new_matched_tokens(
        req2, num_computed_tokens=gpu_local_computed
    )
    # CPU should hit blocks 2,3 (not 4,5 — those are beyond the CPU range).
    num_cpu_hit_blocks = 2
    # Actually CPU has all 6 stored; it returns hits starting from position 2.
    # The number of CPU hit blocks = min(remaining request blocks, CPU cached).
    # Here remaining = 6 - 2 = 4 blocks are in CPU, so hit = 4 * BLOCK_SIZE.
    num_cpu_hit_blocks = 4
    assert hit_tokens == num_cpu_hit_blocks * BLOCK_SIZE, (
        f"Expected {num_cpu_hit_blocks * BLOCK_SIZE} CPU hit tokens, got {hit_tokens}"
    )
    assert is_async is True

    # Simulate what the real scheduler does: only accept 2 of the 4 CPU hit
    # blocks as external (e.g. due to budget constraints), leaving 2 new
    # blocks for fresh compute.
    num_ext_blocks = 2
    num_new_blocks = 2
    external_tokens = num_ext_blocks * BLOCK_SIZE

    # Build block list matching real layout: | comp(2) | ext_comp(2) | new(2) |
    # comp: GPU prefix cache hit — blocks with hashes
    gpu_comp = _allocate_gpu_blocks(gpu_pool, req2, 2, group_id=0)
    # ext_comp + new: freshly allocated, no hashes
    gpu_ext_and_new = gpu_pool.get_new_blocks(num_ext_blocks + num_new_blocks)
    all_gpu_blocks = gpu_comp + gpu_ext_and_new
    kv_blocks2 = KVCacheBlocks(blocks=(all_gpu_blocks,))

    # Critical call: with 2 hashed comp blocks and 2 external tokens worth
    # of blocks, the manager must derive skipped=2 and load hashes [2,3].
    sched.update_state_after_alloc(
        req2, kv_blocks2, num_external_tokens=external_tokens
    )

    block_ids2 = kv_blocks2.get_block_ids()
    sched_out2 = make_scheduler_output(
        {req2.request_id: num_new_blocks * BLOCK_SIZE},
        new_reqs={req2.request_id: block_ids2},
    )
    meta2 = sched.build_connector_meta(sched_out2)
    assert meta2.load_event >= 0, "Expected a load event for partial GPU + CPU hit"
    assert len(meta2.load_gpu_blocks) == num_ext_blocks
    assert len(meta2.load_cpu_blocks) == num_ext_blocks

    # Verify the load targets the ext_comp GPU blocks (positions 2,3),
    # not the comp blocks (0,1) or new blocks (4,5).
    ext_block_ids = [b.block_id for b in gpu_ext_and_new[:num_ext_blocks]]
    for bid in meta2.load_gpu_blocks:
        assert bid in ext_block_ids, (
            f"Load GPU block {bid} should be an ext_comp block, not a comp or new block"
        )