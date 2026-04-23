async def test_cache_cross_compatibility_stream_to_create() -> None:
    """Test that create_stream() cache can be used by create() call.
    This tests the scenario where:
    1. User calls create_stream() - stores List[Union[str, CreateResult]]
    2. User calls create() with same inputs - should get cache hit and return the final CreateResult
    """
    _, prompts, system_prompt, _, cached_client = get_test_data()

    # First call: create_stream() - should cache a List[Union[str, CreateResult]]
    first_stream_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        first_stream_results.append(copy.copy(chunk))

    # Verify we got streaming results
    assert len(first_stream_results) > 0
    final_create_result = None
    for item in first_stream_results:
        if isinstance(item, CreateResult):
            final_create_result = item
            break

    assert final_create_result is not None
    assert not final_create_result.cached  # First call should not be cached

    # Second call: create() with same inputs - should hit the streaming cache
    create_result = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])

    assert isinstance(create_result, CreateResult)
    assert create_result.cached  # Should be marked as cached
    assert create_result.content == final_create_result.content

    # Verify no additional API calls were made (cache hit)
    initial_usage = cached_client.total_usage()

    # Third call: create() again - should still hit cache
    create_result_2 = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])

    # Usage should be the same (no new API calls)
    assert cached_client.total_usage().prompt_tokens == initial_usage.prompt_tokens
    assert cached_client.total_usage().completion_tokens == initial_usage.completion_tokens
    assert create_result_2.cached