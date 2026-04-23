def test_priority_scheduling_no_preemption_when_space_available():
    """Test that preemption doesn't happen
    when there's space for new requests."""
    scheduler = create_scheduler_with_priority(
        max_num_seqs=3,  # Allow 3 concurrent requests
        max_num_batched_tokens=200,  # Sufficient token budget
    )

    # Add two low-priority running requests
    low_priority_requests = create_requests_with_priority(
        num_requests=2,
        priorities=[5, 5],
        arrival_times=[1.0, 2.0],
        num_tokens=30,
        req_ids=["lo1", "lo2"],
    )

    for request in low_priority_requests:
        scheduler.add_request(request)

    output = scheduler.schedule()
    model_output = ModelRunnerOutput(
        req_ids=[req.request_id for req in low_priority_requests],
        req_id_to_index={
            req.request_id: i for i, req in enumerate(low_priority_requests)
        },
        sampled_token_ids=[[100] for _ in low_priority_requests],
        logprobs=None,
        prompt_logprobs_dict={},
        pooler_output=[],
    )
    scheduler.update_from_output(output, model_output)

    # Add high-priority request
    high_priority_request = create_requests_with_priority(
        num_requests=1,
        priorities=[0],
        arrival_times=[3.0],
        num_tokens=30,
        req_ids=["hi1"],
    )[0]

    scheduler.add_request(high_priority_request)

    # Schedule - should not preempt since there's space
    output = scheduler.schedule()

    # Should schedule the new request without preemption
    assert len(output.scheduled_new_reqs) == 1
    assert len(scheduler.running) == 3  # All three requests running
    assert len(scheduler.waiting) == 0