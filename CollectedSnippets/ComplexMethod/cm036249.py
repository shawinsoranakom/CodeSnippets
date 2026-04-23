def test_scheduler_reset_prefix_cache():
    scheduler = create_scheduler(enable_prefix_caching=True)
    requests = create_requests(num_requests=10)
    for request in requests:
        scheduler.add_request(request)

    # Initial scheduling, requests should be at the running state now
    _ = scheduler.schedule()

    # Verify requests moved from waiting to running
    assert len(scheduler.waiting) == 0
    assert len(scheduler.running) == len(requests)
    for i, request in enumerate(requests):
        assert scheduler.running[i] == request

    # Reset prefix cache should fail since there are still running requests
    # and they are taking KV cache
    assert not scheduler.reset_prefix_cache()

    # Reset prefix cache with reset_running_requests=True. All running requests
    # Should be pushed back to the waiting queue and kv cache should be freed
    assert scheduler.reset_prefix_cache(reset_running_requests=True)

    # Verify requests moved from running to waiting
    assert len(scheduler.waiting) == len(requests)
    assert len(scheduler.running) == 0

    for i, request in enumerate(requests):
        assert scheduler.waiting[i] == request