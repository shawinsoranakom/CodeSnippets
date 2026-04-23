def test_priority_scheduling_preemption_and_resumption_when_out_of_kv(
    use_ec_connector, ec_role
):
    """Test that priority scheduling preempts lower priority requests
    when out of KV cache space."""
    # Create scheduler with very limited memory to force preemption
    scheduler = create_scheduler_with_priority(
        max_num_seqs=2,  # Allow multiple requests
        max_num_batched_tokens=200,
        num_blocks=5,  # Can hold 64 tokens (first block is null)
        block_size=16,  # Standard block size
        use_kv_connector=True,
        # encoder connector should not affect test results
        use_ec_connector=use_ec_connector,
        ec_role=ec_role,
    )

    # Create a request and schedule it
    request_low = create_requests_with_priority(
        num_requests=1,
        priorities=[1],
        arrival_times=[0.0],
        num_tokens=30,
        starting_idx=0,
    )[0]
    scheduler.add_request(request_low)
    # 1st schedule
    output = scheduler.schedule()
    assert len(output.scheduled_new_reqs) == 1
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 1

    # Simulate model execution - 1st decode
    model_output = ModelRunnerOutput(
        req_ids=[request_low.request_id],
        req_id_to_index={request_low.request_id: 0},
        sampled_token_ids=[[100]],
        # spec_token_ids=None,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_output)

    # Create a high priority request and schedule it
    request_high = create_requests_with_priority(
        num_requests=1,
        priorities=[0],
        arrival_times=[1.0],
        num_tokens=32,
        starting_idx=1,
    )[0]
    scheduler.add_request(request_high)
    # 2nd schedule
    output = scheduler.schedule()
    # KV cache should be full at this point
    assert scheduler.kv_cache_manager.block_pool.get_num_free_blocks() == 0
    assert len(output.scheduled_new_reqs) == 1
    assert output.scheduled_cached_reqs.num_reqs == 1
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 2

    # Simulate model execution - 2nd decode
    requests = [request_low, request_high]
    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[[100] for _ in requests],
        # spec_token_ids=None,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_output)

    # 3rd schedule - this should trigger preemption
    # req_low needs 32 tokens = 2 blocks
    # req_high needs 33 tokens = 3 blocks
    # so doesn't fit in 4 blocks.
    output = scheduler.schedule()

    # Should have preempted req_low
    assert len(output.scheduled_new_reqs) == 0
    assert output.scheduled_cached_reqs.num_reqs == 1
    assert output.scheduled_cached_reqs.req_ids[0] == request_high.request_id
    assert scheduler.requests[request_low.request_id].status == RequestStatus.PREEMPTED
    assert len(scheduler.waiting) == 1
    assert len(scheduler.running) == 1

    # Simulate model execution - 3rd decode
    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in requests],
        req_id_to_index={req.request_id: i for i, req in enumerate(requests)},
        sampled_token_ids=[[], [100]],
        # spec_token_ids=None,
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    # Finish the requests to make room for the preempted requests to resume
    scheduler.update_from_output(output, model_output)
    scheduler.finish_requests(request_high.request_id, RequestStatus.FINISHED_STOPPED)

    # 4th Schedule - this should trigger the resumption
    output = scheduler.schedule()
    scheduled_cached_reqs = output.scheduled_cached_reqs

    assert len(output.scheduled_new_reqs) == 0
    assert scheduled_cached_reqs.num_reqs == 1
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == 1

    # Preempted request resumed in scheduled_cached_reqs
    assert len(scheduled_cached_reqs.resumed_req_ids) == 1
    assert len(scheduled_cached_reqs.all_token_ids) == 1
    assert scheduled_cached_reqs.req_ids[0] == request_low.request_id
    assert request_low.request_id in scheduled_cached_reqs.resumed_req_ids
    assert request_low.request_id in scheduled_cached_reqs.all_token_ids
    # Resumed tokens include 30 prompt tokens and 2 decoded tokens
    assert len(scheduled_cached_reqs.all_token_ids[request_low.request_id]) == 32
    assert scheduled_cached_reqs.all_token_ids[request_low.request_id][31] == 100