def test_priority_scheduling_equal_priority_preemption():
    """Test arrival time tiebreaker when requests have equal priority."""
    # This test verifies that arrival time is used as a tiebreaker for equal
    # priorities
    scheduler = create_scheduler_with_priority(
        max_num_seqs=1,  # Force sequential processing
    )

    # Create requests with same priority but different arrival times
    requests = create_requests_with_priority(
        num_requests=3,
        priorities=[2, 2, 2],  # Same priority
        arrival_times=[3.0, 1.0, 2.0],  # Different arrival times
        num_tokens=10,
    )

    # Add all requests
    for request in requests:
        scheduler.add_request(request)

    # Schedule - should schedule the request with earliest arrival time
    output = scheduler.schedule()
    assert len(output.scheduled_new_reqs) == 1
    assert output.scheduled_new_reqs[0].req_id == "1"  # Earliest arrival (1.0)

    # Verify the waiting queue has remaining requests in arrival time order
    assert len(scheduler.waiting) == 2

    # Extract waiting requests and verify arrival time order
    waiting_requests = list(scheduler.waiting)

    waiting_arrival_times = [req.arrival_time for req in waiting_requests]
    waiting_req_ids = [req.request_id for req in waiting_requests]

    # Should be req_2 (arrival 2.0) then req_0 (arrival 3.0)
    assert waiting_arrival_times == [2.0, 3.0]
    assert waiting_req_ids == ["2", "0"]