def test_async_load_failure(
    scheduler: Scheduler,
    num_prompt_blocks: int,
    num_external_computed_blocks: int,
    invalid_block_idxs: set[int],
):
    assert num_prompt_blocks >= num_external_computed_blocks

    num_prompt_tokens = num_prompt_blocks * scheduler.block_size
    num_external_computed_tokens = num_external_computed_blocks * scheduler.block_size

    request1 = create_request(num_tokens=num_prompt_tokens)
    scheduler.add_request(request=request1)
    request2 = create_request(num_tokens=num_prompt_tokens)
    scheduler.add_request(request=request2)
    request3 = create_request(num_tokens=num_prompt_tokens)
    scheduler.add_request(request=request3)

    # Mock KV connector method.
    # req_id -> num_external_computed_tokens
    req_num_new_matched_tokens = {
        request1.request_id: num_external_computed_tokens,
        request2.request_id: num_external_computed_tokens,
        request3.request_id: num_external_computed_tokens,
    }

    scheduler.connector = Mock()
    scheduler.connector.get_num_new_matched_tokens.side_effect = (
        _make_get_num_new_matched_tokens(req_num_new_matched_tokens, async_load=True)
    )
    scheduler.connector.take_events.return_value = ()

    scheduler_output = scheduler.schedule()

    assert len(scheduler.waiting) == 0
    assert len(scheduler.skipped_waiting) == 3
    for request in scheduler.skipped_waiting:
        assert request.num_computed_tokens == num_external_computed_tokens
        assert request.status == RequestStatus.WAITING_FOR_REMOTE_KVS
    assert scheduler.connector.get_num_new_matched_tokens.call_count == 3

    # Simulate a failure in loading some of request2 blocks.
    (req2_block_ids,) = scheduler.kv_cache_manager.get_block_ids(request2.request_id)
    invalid_block_ids = {req2_block_ids[i] for i in invalid_block_idxs}
    model_runner_output = create_model_runner_output(
        reqs=[],
        finished_recving={request1.request_id, request3.request_id},
        invalid_block_ids=invalid_block_ids,
        use_eos=True,
    )

    scheduler.update_from_output(scheduler_output, model_runner_output)

    min_invalid_block_idx = min(invalid_block_idxs)

    assert len(scheduler.waiting) == 0
    assert len(scheduler.skipped_waiting) == 3
    for request in scheduler.skipped_waiting:
        if request.request_id == request2.request_id:
            assert request.num_computed_tokens == (
                min_invalid_block_idx * scheduler.block_size
            )
        else:
            assert request.num_computed_tokens == num_external_computed_tokens
        assert request.status == RequestStatus.WAITING_FOR_REMOTE_KVS
    assert scheduler.failed_recving_kv_req_ids == {request2.request_id}
    assert scheduler.connector.get_num_new_matched_tokens.call_count == 3