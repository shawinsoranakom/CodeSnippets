def test_priority_scheduling_waiting_queue_order():
    """Test that the waiting queue maintains priority order."""
    scheduler = create_scheduler_with_priority(
        max_num_seqs=1,  # Only one request can run at a time
    )

    # Create multiple requests with different priorities
    requests = create_requests_with_priority(
        num_requests=4,
        priorities=[3, 1, 2, 0],  # Mixed priorities
        arrival_times=[1.0, 2.0, 3.0, 4.0],
        num_tokens=10,
    )

    # Add all requests
    for request in requests:
        scheduler.add_request(request)

    # Schedule - should only schedule the highest priority request
    # (req_3, priority 0)
    output = scheduler.schedule()
    assert len(output.scheduled_new_reqs) == 1
    assert output.scheduled_new_reqs[0].req_id == "3"

    # Verify waiting queue has remaining requests in priority order
    assert len(scheduler.waiting) == 3

    # Extract requests from waiting queue
    # (it's a heap, so we need to pop to see order)
    waiting_requests = list(scheduler.waiting)

    waiting_priorities = [req.priority for req in waiting_requests]
    waiting_req_ids = [req.request_id for req in waiting_requests]

    # Should be ordered by priority: req_1 (1), req_2 (2), req_0 (3)
    assert waiting_req_ids == ["1", "2", "0"]
    assert waiting_priorities == [1, 2, 3]