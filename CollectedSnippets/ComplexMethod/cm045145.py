async def test_cache_cross_compatibility_create_to_stream() -> None:
    """Test that create() cache can be used by create_stream() call.
    This tests the scenario where:
    1. User calls create() - stores CreateResult
    2. User calls create_stream() with same inputs - should get cache hit and yield the CreateResult
    """
    responses, prompts, system_prompt, _, cached_client = get_test_data()

    # First call: create() - should cache a CreateResult
    create_result = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert isinstance(create_result, CreateResult)
    assert not create_result.cached
    assert create_result.content == responses[0]

    # Second call: create_stream() with same inputs - should hit the cache
    stream_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        stream_results.append(copy.copy(chunk))

    # Should yield exactly two items: the string content + the cached CreateResult
    assert len(stream_results) == 2

    # First item should be the string content
    assert isinstance(stream_results[0], str)
    assert stream_results[0] == responses[0]

    # Second item should be the cached CreateResult
    assert isinstance(stream_results[1], CreateResult)
    assert stream_results[1].cached  # Should be marked as cached
    assert stream_results[1].content == responses[0]

    # Verify no additional API calls were made (cache hit)
    initial_usage = cached_client.total_usage()

    # Third call: create_stream() again - should still hit cache
    stream_results_2: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        stream_results_2.append(copy.copy(chunk))

    # Usage should be the same (no new API calls)
    assert cached_client.total_usage().prompt_tokens == initial_usage.prompt_tokens
    assert cached_client.total_usage().completion_tokens == initial_usage.completion_tokens