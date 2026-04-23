async def test_async_wait(rate_limiter: InMemoryRateLimiter) -> None:
    with freeze_time("2023-01-01 00:00:00") as frozen_time:
        rate_limiter.last = time.time()
        assert not await rate_limiter.aacquire(blocking=False)
        frozen_time.tick(0.1)  # Increment by 0.1 seconds
        assert rate_limiter.available_tokens == 0
        assert not await rate_limiter.aacquire(blocking=False)
        frozen_time.tick(0.1)  # Increment by 0.1 seconds
        assert rate_limiter.available_tokens == 0
        assert not await rate_limiter.aacquire(blocking=False)
        frozen_time.tick(1.8)
        assert await rate_limiter.aacquire(blocking=False)
        assert rate_limiter.available_tokens == 1.0
        assert await rate_limiter.aacquire(blocking=False)
        assert rate_limiter.available_tokens == 0
        frozen_time.tick(2.1)
        assert await rate_limiter.aacquire(blocking=False)
        assert rate_limiter.available_tokens == 1
        frozen_time.tick(0.9)
        assert await rate_limiter.aacquire(blocking=False)
        assert rate_limiter.available_tokens == 1