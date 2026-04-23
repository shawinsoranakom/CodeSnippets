def test_async_recompute_blocks_not_cached_when_invalid(
    recompute_scheduler: Scheduler,
):
    """
    Test async recompute case - invalid blocks not cached after transfer.

    When async KV loading has invalid blocks and retry_policy is 'recompute':
    1. Blocks are allocated but not cached yet
    2. When async transfer completes, only valid blocks should be cached
    3. Invalid blocks should never enter the prefix cache

    This test verifies correctness, the failed_recving_kv_req_ids protection
    ensures only valid blocks are cached when the transfer completes, and we
    only evict blocks from cache that are already hashed in the block table.
    """
    from unittest.mock import patch

    num_prompt_blocks = 100
    num_external_computed_blocks = 99
    invalid_block_idx = 50

    num_prompt_tokens = num_prompt_blocks * recompute_scheduler.block_size
    num_external_computed_tokens = (
        num_external_computed_blocks * recompute_scheduler.block_size
    )

    request = create_request(num_tokens=num_prompt_tokens)
    recompute_scheduler.add_request(request=request)

    req_num_new_matched_tokens = {
        request.request_id: num_external_computed_tokens,
    }

    # mock connector indicating async load
    recompute_scheduler.connector = Mock()
    recompute_scheduler.connector.get_num_new_matched_tokens.side_effect = (
        _make_get_num_new_matched_tokens(req_num_new_matched_tokens, True)
    )
    recompute_scheduler.connector.request_finished.return_value = (False, None)
    recompute_scheduler.connector.take_events.return_value = ()

    scheduler_output = recompute_scheduler.schedule()

    # request should be waiting for remote KVs
    assert len(recompute_scheduler.skipped_waiting) == 1
    assert request.status == RequestStatus.WAITING_FOR_REMOTE_KVS
    assert request.num_computed_tokens == num_external_computed_tokens

    # get the allocated block IDs
    (req_block_ids,) = recompute_scheduler.kv_cache_manager.get_block_ids(
        request.request_id
    )
    invalid_block_id = req_block_ids[invalid_block_idx]
    invalid_block_ids = {invalid_block_id}

    # get the block object to verify it's not cached yet and stays uncached
    block = recompute_scheduler.kv_cache_manager.block_pool.blocks[invalid_block_id]

    # verify block has no hash before invalid blocks are reported
    assert block.block_hash is None, (
        "Async loading blocks should not be cached yet (no hash)"
    )

    # report invalid blocks (transfer not finished yet)
    model_runner_output = create_model_runner_output(
        reqs=[],
        finished_recving=None,  # transfer NOT finished
        invalid_block_ids=invalid_block_ids,
        use_eos=False,
    )

    # critical: spy on evict_blocks to verify it's NOT called for async blocks
    original_evict_blocks = recompute_scheduler.kv_cache_manager.evict_blocks
    evict_blocks_calls = []

    def evict_blocks_spy(block_ids):
        evict_blocks_calls.append(set(block_ids))
        return original_evict_blocks(block_ids)

    with patch.object(
        recompute_scheduler.kv_cache_manager, "evict_blocks", evict_blocks_spy
    ):
        outputs = recompute_scheduler.update_from_output(
            scheduler_output, model_runner_output
        )

    # verify evict_blocks was NOT called (async blocks excluded from eviction)
    assert len(evict_blocks_calls) == 0, (
        f"evict_blocks should not be called for async-only invalid blocks, "
        f"but was called {len(evict_blocks_calls)} time(s) with {evict_blocks_calls}"
    )

    # request should still be waiting (not finished with error due to recompute policy)
    assert request.status == RequestStatus.WAITING_FOR_REMOTE_KVS
    assert request.request_id in recompute_scheduler.failed_recving_kv_req_ids

    # verify num_computed_tokens was truncated to before invalid block
    expected_valid_tokens = invalid_block_idx * recompute_scheduler.block_size
    assert request.num_computed_tokens == expected_valid_tokens

    # verify invalid block still has no hash (was not evicted)
    assert block.block_hash is None, (
        f"Async loading blocks shouldn't be cached or evicted. "
        f"Block {invalid_block_id} hash should be None but is {block.block_hash}"
    )

    # Verify connector prefix cache stats:
    # - queries = num_prompt_tokens (total tokens not in local cache)
    # - hits = num_external_computed_tokens (tokens loaded externally)
    assert len(outputs) == 1
    engine_outputs = next(iter(outputs.values()))
    assert engine_outputs.scheduler_stats is not None
    stats = engine_outputs.scheduler_stats
    assert stats.connector_prefix_cache_stats is not None
    conn_stats = stats.connector_prefix_cache_stats
    assert conn_stats.requests == 1
    assert conn_stats.queries == num_prompt_tokens
    assert conn_stats.hits == num_external_computed_tokens

    # now simulate async transfer completing
    model_runner_output_2 = create_model_runner_output(
        reqs=[],
        finished_recving={request.request_id},
        invalid_block_ids=None,
        use_eos=False,
    )

    recompute_scheduler.update_from_output(scheduler_output, model_runner_output_2)

    # verify request is now marked as finished receiving and ready to be processed
    assert request.request_id in recompute_scheduler.finished_recving_kv_req_ids
    assert request.request_id in recompute_scheduler.failed_recving_kv_req_ids

    # critical: verify invalid block still has no hash before recompute
    # the async transfer invalid data was never cached
    assert block.block_hash is None, (
        f"Invalid block {invalid_block_id} should not be cached before recompute "
        f"(hash should be None), but hash is {block.block_hash}"
    )

    # critical end-to-end test: spy on cache_blocks to verify it's called with
    # the truncated num_computed_tokens value
    original_cache_blocks = recompute_scheduler.kv_cache_manager.cache_blocks
    cache_blocks_calls = []

    def cache_blocks_spy(req, num_tokens):
        cache_blocks_calls.append((req.request_id, num_tokens))
        return original_cache_blocks(req, num_tokens)

    with patch.object(
        recompute_scheduler.kv_cache_manager, "cache_blocks", cache_blocks_spy
    ):
        # call schedule() again - this triggers _update_waiting_for_remote_kv()
        # which should call cache_blocks with the truncated value
        recompute_scheduler.schedule()

    # verify cache_blocks was called with the truncated value
    assert len(cache_blocks_calls) == 1, (
        f"cache_blocks should be called exactly once, "
        f"got {len(cache_blocks_calls)} calls"
    )
    cached_req_id, cached_num_tokens = cache_blocks_calls[0]
    assert cached_req_id == request.request_id
    assert cached_num_tokens == expected_valid_tokens, (
        f"cache_blocks should be called with truncated value {expected_valid_tokens}, "
        f"but was called with {cached_num_tokens}"
    )

    # request should now be RUNNING (scheduled immediately after transfer completes)
    # the flow is: WAITING_FOR_REMOTE_KVS -> WAITING -> RUNNING in same schedule() call
    assert request.status == RequestStatus.RUNNING

    # num_computed_tokens should be >= expected_valid_tokens because the scheduler
    # will schedule additional new tokens (up to max_num_batched_tokens) for the request
    assert request.num_computed_tokens >= expected_valid_tokens, (
        f"num_computed_tokens should be at least {expected_valid_tokens}, "
        f"got {request.num_computed_tokens}"
    )

    # request should no longer be in the failed/finished receiving sets
    assert request.request_id not in recompute_scheduler.failed_recving_kv_req_ids
    assert request.request_id not in recompute_scheduler.finished_recving_kv_req_ids

    # request should be in the running queue
    assert request in recompute_scheduler.running