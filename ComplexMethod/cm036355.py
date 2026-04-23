def test_sync_recompute_blocks_not_freed_for_running_requests(
    recompute_scheduler: Scheduler,
):
    """
    Test sync recompute case - blocks must not be freed for running requests.

    When a running request has invalid blocks and retry_policy is 'recompute':
    1. Request should remain in RUNNING state
    2. num_computed_tokens should be truncated to invalid block boundary
    3. Blocks should NOT be freed (request still needs them for recomputation)
    4. Request should remain in scheduler.requests and scheduler.running
    """
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

    # mock connector indicating sync load
    recompute_scheduler.connector = Mock()
    recompute_scheduler.connector.get_num_new_matched_tokens.side_effect = (
        _make_get_num_new_matched_tokens(req_num_new_matched_tokens, False)
    )
    recompute_scheduler.connector.request_finished.return_value = (False, None)
    recompute_scheduler.connector.take_events.return_value = ()

    scheduler_output = recompute_scheduler.schedule()

    # request should be running with sync KV load
    assert len(recompute_scheduler.running) == 1
    assert len(scheduler_output.scheduled_new_reqs) == 1
    assert request.status == RequestStatus.RUNNING

    # get the allocated block IDs before invalid blocks are reported
    req_block_ids = scheduler_output.scheduled_new_reqs[0].block_ids[0]
    invalid_block_ids = {req_block_ids[invalid_block_idx]}

    # store original num_computed_tokens for comparison
    original_num_computed_tokens = request.num_computed_tokens

    model_runner_output = create_model_runner_output(
        [request],
        invalid_block_ids=invalid_block_ids,
        use_eos=False,  # not finished - should continue running
    )

    outputs = recompute_scheduler.update_from_output(
        scheduler_output, model_runner_output
    )

    # critical assertions for recompute case:

    # 1. request should still be RUNNING (not finished, not aborted)
    assert request.status == RequestStatus.RUNNING, (
        f"Request should remain RUNNING for recompute, got {request.status}"
    )

    # 2. num_computed_tokens should be truncated to first invalid block
    expected_truncated_tokens = invalid_block_idx * recompute_scheduler.block_size
    assert request.num_computed_tokens == expected_truncated_tokens, (
        f"num_computed_tokens should be truncated to {expected_truncated_tokens}, "
        f"got {request.num_computed_tokens}"
    )
    assert request.num_computed_tokens < original_num_computed_tokens, (
        "num_computed_tokens should be reduced after invalid block detection"
    )

    # 3. no output should be generated (request is still running)
    # the request should be skipped in the output loop
    assert len(outputs) == 0 or request.request_id not in [
        out.request_id for outs in outputs.values() for out in outs.outputs
    ], "No output should be generated for recompute requests"

    # 4. request should still be in running queue
    assert request in recompute_scheduler.running, (
        "Request should remain in running queue for recomputation"
    )

    # 5. request should still be in scheduler.requests (not deleted)
    assert request.request_id in recompute_scheduler.requests, (
        "Request should not be deleted from scheduler.requests"
    )

    # 6. blocks should NOT be freed - verify blocks are still allocated
    try:
        allocated_blocks = recompute_scheduler.kv_cache_manager.get_block_ids(
            request.request_id
        )
        assert allocated_blocks is not None
        assert len(allocated_blocks[0]) > 0, (
            "Blocks should still be allocated for recomputation"
        )
    except KeyError:
        pytest.fail(
            "Blocks were freed incorrectly! Running requests need their blocks "
            "to recompute invalid portions."
        )

    # 7. verify request can be rescheduled in next step
    scheduler_output_2 = recompute_scheduler.schedule()

    # request should appear in the new schedule to recompute invalid blocks
    scheduled_req_ids = [
        req.request_id for req in scheduler_output_2.scheduled_new_reqs
    ]
    if scheduler_output_2.num_scheduled_tokens:
        scheduled_req_ids.extend(scheduler_output_2.num_scheduled_tokens.keys())

    assert (
        request.request_id in scheduled_req_ids or len(recompute_scheduler.running) > 0
    ), "Request should be reschedulable for recomputation"