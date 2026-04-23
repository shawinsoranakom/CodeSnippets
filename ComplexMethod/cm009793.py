def test_sync_wait(rate_limiter: InMemoryRateLimiter) -> None:
    with freeze_time("2023-01-01 00:00:00") as frozen_time:
        rate_limiter.last = time.time()
        assert not rate_limiter.acquire(blocking=False)
        frozen_time.tick(0.1)  # Increment by 0.1 seconds
        assert rate_limiter.available_tokens == 0
        assert not rate_limiter.acquire(blocking=False)
        frozen_time.tick(0.1)  # Increment by 0.1 seconds
        assert rate_limiter.available_tokens == 0
        assert not rate_limiter.acquire(blocking=False)
        frozen_time.tick(1.8)
        assert rate_limiter.acquire(blocking=False)
        assert rate_limiter.available_tokens == 1.0
        assert rate_limiter.acquire(blocking=False)
        assert rate_limiter.available_tokens == 0
        frozen_time.tick(2.1)
        assert rate_limiter.acquire(blocking=False)
        assert rate_limiter.available_tokens == 1
        frozen_time.tick(0.9)
        assert rate_limiter.acquire(blocking=False)
        assert rate_limiter.available_tokens == 1

        # Check max bucket size
        frozen_time.tick(100)
        assert rate_limiter.acquire(blocking=False)
        assert rate_limiter.available_tokens == 1