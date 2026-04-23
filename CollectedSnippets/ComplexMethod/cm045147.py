async def test_cache_cross_compatibility_mixed_sequence() -> None:
    """Test mixed sequence of create() and create_stream() calls with caching.
    This tests a realistic scenario with multiple interleaved calls:
    create() → create_stream() → create() → create_stream()
    """
    responses, prompts, system_prompt, _, cached_client = get_test_data(num_messages=4)

    # Call 1: create() with prompt[0] - should make API call
    result1 = await cached_client.create([system_prompt, UserMessage(content=prompts[0], source="user")])
    assert not result1.cached
    assert result1.content == responses[0]
    usage_after_1 = copy.copy(cached_client.total_usage())

    # Call 2: create_stream() with prompt[0] - should hit cache from call 1
    stream1_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        stream1_results.append(chunk)

    assert len(stream1_results) == 2  # Should yield string content + cached CreateResult
    assert isinstance(stream1_results[0], str)  # First item: string content
    assert stream1_results[0] == responses[0]
    assert isinstance(stream1_results[1], CreateResult)  # Second item: cached CreateResult
    assert stream1_results[1].cached
    usage_after_2 = copy.copy(cached_client.total_usage())
    # No new API call should have been made
    assert usage_after_2.prompt_tokens == usage_after_1.prompt_tokens

    # Call 3: create_stream() with prompt[1] - should make new API call
    stream2_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[1], source="user")]):
        stream2_results.append(copy.copy(chunk))

    # Should have made a new API call
    usage_after_3 = copy.copy(cached_client.total_usage())
    assert usage_after_3.prompt_tokens > usage_after_2.prompt_tokens

    # Find the final CreateResult
    final_result = None
    for item in stream2_results:
        if isinstance(item, CreateResult):
            final_result = item
            break
    assert final_result is not None
    assert not final_result.cached

    # Call 4: create() with prompt[1] - should hit cache from call 3
    result4 = await cached_client.create([system_prompt, UserMessage(content=prompts[1], source="user")])
    assert result4.cached
    assert result4.content == final_result.content
    usage_after_4 = copy.copy(cached_client.total_usage())
    # No new API call should have been made
    assert usage_after_4.prompt_tokens == usage_after_3.prompt_tokens