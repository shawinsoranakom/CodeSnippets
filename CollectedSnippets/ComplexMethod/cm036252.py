def test_scheduler_stats_waiting_queues():
    """Test that scheduler stats correctly report waiting and skipped_waiting queues."""
    # Create scheduler with limited capacity so we can have waiting requests
    scheduler = create_scheduler(max_num_batched_tokens=100)

    # Create requests: some will be scheduled, some will wait on capacity,
    # and some will be blocked by constraints
    all_requests = create_requests(num_requests=5, num_tokens=50)

    # Add 3 requests - only 2 can be scheduled (2 * 50 = 100 tokens)
    # The 3rd will remain in waiting queue (capacity constraint)
    for request in all_requests[:3]:
        scheduler.add_request(request)

    # Manually add 2 more to skipped_waiting to simulate constraint-blocked
    for request in all_requests[3:]:
        request.status = RequestStatus.WAITING_FOR_REMOTE_KVS
        scheduler.skipped_waiting.add_request(request)

    # Schedule - this will schedule 2 requests, leaving 1 in waiting
    output = scheduler.schedule()

    # Verify: 2 scheduled, 1 still waiting on capacity, 2 blocked by constraints
    assert len(output.scheduled_new_reqs) == 2
    assert len(scheduler.waiting) == 1
    assert len(scheduler.skipped_waiting) == 2

    # Call update_from_output() to get frontend-facing stat
    scheduled_req_ids = list(output.num_scheduled_tokens.keys())
    model_runner_output = ModelRunnerOutput(
        req_ids=scheduled_req_ids,
        req_id_to_index={req_id: i for i, req_id in enumerate(scheduled_req_ids)},
        sampled_token_ids=[[1]] * len(scheduled_req_ids),
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    engine_core_outputs = scheduler.update_from_output(output, model_runner_output)
    assert engine_core_outputs and len(engine_core_outputs) > 0
    stats = engine_core_outputs[0].scheduler_stats
    assert stats is not None

    # Verify stats match queue lengths after scheduling
    assert stats.num_running_reqs == 2  # 2 were scheduled
    assert stats.num_waiting_reqs == 1  # 1 waiting on capacity
    assert stats.num_skipped_waiting_reqs == 2