async def test_redis_streaming_cache_integration() -> None:
    """Integration test for Redis streaming cache scenario.
    This test covers the original streaming cache issues:
    1. Cache is stored after streaming completes (not before)
    2. Redis cache properly handles lists containing CreateResult objects
    3. ChatCompletionCache properly reconstructs CreateResult from Redis dicts
    """
    from unittest.mock import MagicMock

    # Skip this test if redis is not available
    pytest.importorskip("redis")

    from autogen_ext.cache_store.redis import RedisStore

    # Use standardized test data
    _, prompts, system_prompt, replay_client, _ = get_test_data()

    # Mock Redis instance to control what gets stored/retrieved
    redis_instance = MagicMock()
    redis_store = RedisStore[CHAT_CACHE_VALUE_TYPE](redis_instance)

    # Create the cached client with Redis store
    cached_client = ChatCompletionCache(replay_client, redis_store)

    # Simulate first streaming call (should cache after completion)
    first_stream_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        first_stream_results.append(copy.copy(chunk))

    # Verify Redis set was called with the complete streaming results
    redis_instance.set.assert_called_once()
    call_args = redis_instance.set.call_args
    serialized_data = call_args[0][1]

    # Verify the serialized data represents the complete stream
    assert isinstance(serialized_data, bytes)
    import json

    deserialized = json.loads(serialized_data.decode("utf-8"))
    assert isinstance(deserialized, list)
    # Type narrowing: after isinstance check, deserialized is known to be a list
    deserialized_list: List[Union[str, Dict[str, Union[str, int]]]] = deserialized  # Now properly typed as list
    # Should contain both string chunks and final CreateResult (as dict)
    assert len(deserialized_list) > 0

    # Reset the mock for the second call
    redis_instance.reset_mock()

    # Configure Redis to return the serialized data (simulating cache hit)
    redis_instance.get.return_value = serialized_data

    # Second streaming call should hit the cache
    second_stream_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        second_stream_results.append(copy.copy(chunk))

    # Verify Redis get was called but set was not (cache hit)
    redis_instance.get.assert_called_once()
    redis_instance.set.assert_not_called()

    # Verify both streams have the same content
    assert len(first_stream_results) == len(second_stream_results)

    # Verify cached results are marked as cached
    for first, second in zip(first_stream_results, second_stream_results, strict=True):
        if isinstance(first, CreateResult) and isinstance(second, CreateResult):
            assert not first.cached  # First call should not be cached
            assert second.cached  # Second call should be cached
            assert first.content == second.content
        elif isinstance(first, str) and isinstance(second, str):
            assert first == second
        else:
            pytest.fail(f"Unexpected chunk types: {type(first)}, {type(second)}")