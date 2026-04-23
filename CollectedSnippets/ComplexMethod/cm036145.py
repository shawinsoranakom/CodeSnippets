def test_chunked_prefill_reads_live_block_ids() -> None:
    """With chunked prefill, block IDs accumulate across scheduler steps.
    _prepare_eager_store_specs reads block IDs from scheduler_output via
    yield_req_data, so the store should reflect the updated (larger) block
    list, not a stale snapshot."""
    fix = make_scheduler(num_cpu_blocks=8, num_gpu_blocks=16, lazy=False)
    sched = fix.scheduler

    num_blocks = 4
    req = make_request(num_blocks=num_blocks)

    # First chunk: allocate 2 blocks
    kv_blocks_first = _alloc_and_register(fix, req, 2)
    sched.update_state_after_alloc(req, kv_blocks_first, num_external_tokens=0)

    assert req.request_id in sched._reqs_to_store
    # Should still be exactly 1 entry in _reqs_to_store
    assert list(sched._reqs_to_store.keys()).count(req.request_id) == 1

    # Build connector meta with 2 blocks — stores the first 2
    ids_first = kv_blocks_first.get_block_ids()
    sched_out1 = make_scheduler_output(
        {req.request_id: 2 * BLOCK_SIZE},
        new_reqs={req.request_id: ids_first},
    )
    meta1 = sched.build_connector_meta(sched_out1)
    assert meta1.store_event >= 0
    assert len(meta1.store_gpu_blocks) == 2
    simulate_store_completion(sched, meta1.store_event)

    # Second chunk: allocate 4 blocks total (2 new ones)
    kv_blocks_second = _alloc_and_register(fix, req, num_blocks)
    # update_state_after_alloc is idempotent for store registration
    sched.update_state_after_alloc(req, kv_blocks_second, num_external_tokens=0)

    # Still exactly 1 entry
    assert list(sched._reqs_to_store.keys()).count(req.request_id) == 1

    # The second chunk's NEW block IDs (positions 2,3) are passed as
    # cached_req_new_blocks. The full block_ids include both old and new,
    # but yield_req_data only appends the new_block_ids for cached reqs.
    ids_second_full = kv_blocks_second.get_block_ids()
    # New blocks are those beyond the first chunk
    new_block_ids = tuple(ids_second_full[g][2:] for g in range(len(ids_second_full)))
    sched_out2 = make_scheduler_output(
        {req.request_id: 2 * BLOCK_SIZE},
        cached_req_new_blocks={req.request_id: new_block_ids},
    )
    meta2 = sched.build_connector_meta(sched_out2)
    assert meta2.store_event >= 0
    # Only the 2 NEW blocks should be stored (first 2 already done)
    assert len(meta2.store_gpu_blocks) == 2