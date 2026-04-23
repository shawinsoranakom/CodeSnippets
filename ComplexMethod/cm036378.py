def test_sync_load_failure_with_shared_blocks(
    scheduler: Scheduler,
    num_prompt_blocks: int,
    num_external_computed_blocks: int,
    num_common_prefix_blocks: int,
    invalid_block_idxs: set[int],
):
    assert num_prompt_blocks >= num_external_computed_blocks >= num_common_prefix_blocks

    num_prompt_tokens = num_prompt_blocks * scheduler.block_size
    num_external_computed_tokens = num_external_computed_blocks * scheduler.block_size
    common_prefix_len = num_common_prefix_blocks * scheduler.block_size

    request1 = create_request(
        num_tokens=num_prompt_tokens, common_prefix_len=common_prefix_len
    )
    scheduler.add_request(request=request1)
    request2 = create_request(
        num_tokens=num_prompt_tokens, common_prefix_len=common_prefix_len
    )
    scheduler.add_request(request=request2)

    # Mock KV connector method.
    # req_id -> num_external_computed_tokens
    req_num_new_matched_tokens = {
        request1.request_id: num_external_computed_tokens,
    }

    scheduler.connector = Mock()
    scheduler.connector.get_num_new_matched_tokens.side_effect = (
        _make_get_num_new_matched_tokens(req_num_new_matched_tokens, async_load=False)
    )
    scheduler.connector.take_events.return_value = ()

    scheduler_output = scheduler.schedule()

    # req_id -> num_computed_tokens
    expected_computed_tokens = {
        request1.request_id: num_external_computed_tokens,
        request2.request_id: common_prefix_len,
    }

    assert len(scheduler.running) == 2
    assert len(scheduler_output.scheduled_new_reqs) == 2
    for request in scheduler_output.scheduled_new_reqs:
        assert request.num_computed_tokens == expected_computed_tokens[request.req_id]
    assert scheduler.connector.get_num_new_matched_tokens.call_count == 2

    # Simulate a failure in loading some of the shared blocks.
    req1_block_ids = scheduler_output.scheduled_new_reqs[0].block_ids[0]
    invalid_block_ids = {req1_block_ids[i] for i in invalid_block_idxs}
    model_runner_output = create_model_runner_output(
        [request1, request2], invalid_block_ids=invalid_block_ids, use_eos=True
    )

    scheduler.update_from_output(scheduler_output, model_runner_output)

    # req_id -> num_computed_tokens
    # all the common prefix blocks will be computed by request1
    expected_computed_tokens = {
        request1.request_id: min(invalid_block_idxs) * scheduler.block_size,
        request2.request_id: common_prefix_len,
    }

    assert len(scheduler.running) == 2
    for request in scheduler.running:
        assert (
            request.num_computed_tokens == expected_computed_tokens[request.request_id]
        )
    assert scheduler.connector.get_num_new_matched_tokens.call_count == 2