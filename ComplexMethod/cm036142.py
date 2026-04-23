def test_eager_store_and_load_roundtrip() -> None:
    """Eager mode: store blocks on compute, complete store, verify cache hit."""
    fix = make_scheduler(num_cpu_blocks=8, num_gpu_blocks=16, lazy=False)
    sched = fix.scheduler

    num_blocks = 2
    req = make_request(num_blocks=num_blocks)

    kv_blocks = _alloc_and_register(fix, req, num_blocks)
    sched.update_state_after_alloc(req, kv_blocks, num_external_tokens=0)
    block_ids = kv_blocks.get_block_ids()
    sched_out = make_scheduler_output(
        {req.request_id: num_blocks * BLOCK_SIZE},
        new_reqs={req.request_id: block_ids},
    )

    meta = sched.build_connector_meta(sched_out)
    assert meta.store_event >= 0, "Expected a store event to be scheduled"
    assert len(meta.store_gpu_blocks) > 0
    assert len(meta.store_cpu_blocks) == len(meta.store_gpu_blocks)
    simulate_store_completion(sched, meta.store_event)

    # New request with same tokens should get CPU cache hit
    req2 = Request(
        request_id="req-eager-load",
        prompt_token_ids=req.prompt_token_ids,
        sampling_params=req.sampling_params,
        pooling_params=None,
        mm_features=None,
        block_hasher=req._block_hasher,
    )
    hit_tokens, is_async = sched.get_num_new_matched_tokens(req2, num_computed_tokens=0)
    assert hit_tokens == num_blocks * BLOCK_SIZE
    assert is_async is True

    gpu_blocks2 = fix.gpu_block_pool.get_new_blocks(num_blocks)
    kv_blocks2 = KVCacheBlocks(blocks=(gpu_blocks2,))
    sched.update_state_after_alloc(req2, kv_blocks2, num_external_tokens=hit_tokens)

    block_ids2 = kv_blocks2.get_block_ids()
    sched_out2 = make_scheduler_output(
        {req2.request_id: 1},
        new_reqs={req2.request_id: block_ids2},
    )
    meta2 = sched.build_connector_meta(sched_out2)
    assert meta2.load_event >= 0, "Expected a load event to be assigned"
    assert len(meta2.load_gpu_blocks) > 0
    assert len(meta2.load_cpu_blocks) == len(meta2.load_gpu_blocks)