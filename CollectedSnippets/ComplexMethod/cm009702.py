async def test_rate_limit_astream() -> None:
    """Test rate limiting astream."""
    model = GenericFakeChatModel(
        messages=iter(["hello world", "hello world", "hello world"]),
        rate_limiter=InMemoryRateLimiter(
            requests_per_second=20,
            check_every_n_seconds=0.1,
            max_bucket_size=10,
            # At 20 requests per second we see a refresh every 0.05 seconds
        ),
    )
    # Check astream
    tic = time.time()
    response = [msg async for msg in model.astream("foo")]
    assert [msg.content for msg in response] == ["hello", " ", "world"]
    toc = time.time()
    # Should be larger than check every n seconds since the token bucket starts
    assert 0.1 < toc - tic < 0.2

    # Second time around we should have 1 token left
    tic = time.time()
    response = [msg async for msg in model.astream("foo")]
    assert [msg.content for msg in response] == ["hello", " ", "world"]
    toc = time.time()
    # Should be larger than check every n seconds since the token bucket starts
    assert toc - tic < 0.1  # Slightly smaller than check every n seconds

    # Third time around we should have 0 tokens left
    tic = time.time()
    response = [msg async for msg in model.astream("foo")]
    assert [msg.content for msg in response] == ["hello", " ", "world"]
    toc = time.time()
    assert 0.1 < toc - tic < 0.2