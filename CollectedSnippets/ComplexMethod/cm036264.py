def test_priority_scheduling_with_limited_slots():
    """Test priority scheduling when max_num_seqs limits concurrent requests."""
    scheduler = create_scheduler_with_priority(
        max_num_seqs=2,  # Only allow 2 concurrent requests
        max_num_batched_tokens=1000,  # Plenty of token budget
    )

    # Create requests with different priorities
    requests = create_requests_with_priority(
        num_requests=4,
        priorities=[3, 1, 2, 0],  # Mixed priorities
        arrival_times=[1.0, 2.0, 3.0, 4.0],
        num_tokens=10,
    )

    # Add all requests
    for request in requests:
        scheduler.add_request(request)

    # Schedule - should only schedule the 2 highest priority requests
    output = scheduler.schedule()
    assert len(output.scheduled_new_reqs) == 2

    # Should schedule req_3 (priority 0) and req_1 (priority 1)
    scheduled_req_ids = [req.req_id for req in output.scheduled_new_reqs]
    assert "3" in scheduled_req_ids  # Priority 0
    assert "1" in scheduled_req_ids  # Priority 1

    # Remaining requests should be in waiting queue in priority order
    assert len(scheduler.waiting) == 2

    # Extract waiting requests and verify order
    waiting_requests = list(scheduler.waiting)
    waiting_priorities = [req.priority for req in waiting_requests]
    waiting_req_ids = [req.request_id for req in waiting_requests]

    # Should be req_2 (priority 2) then req_0 (priority 3)
    assert waiting_priorities == [2, 3]
    assert waiting_req_ids == ["2", "0"]