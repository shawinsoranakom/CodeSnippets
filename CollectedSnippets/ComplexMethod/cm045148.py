async def test_create_stream_with_cached_non_streaming_result_string_content() -> None:
    """
    Test that when create_stream() finds a cached non-streaming result with string content,
    it yields both the content string as a streaming chunk and then the CreateResult.
    """
    responses, prompts, system_prompt, replay_client, _ = get_test_data()

    # Create a CreateResult with string content (simulating a cached non-streaming result)
    cached_create_result = CreateResult(
        content=responses[0],  # This is a string
        finish_reason="stop",
        usage=RequestUsage(prompt_tokens=10, completion_tokens=20),
        cached=False,  # Will be set to True when retrieved from cache
    )

    # Mock cache store that returns the non-streaming CreateResult
    mock_store = MockCacheStore(return_value=cached_create_result)
    cached_client = ChatCompletionCache(replay_client, mock_store)

    # Call create_stream() - should yield string content first, then CreateResult
    stream_results: List[Union[str, CreateResult]] = []
    async for chunk in cached_client.create_stream([system_prompt, UserMessage(content=prompts[0], source="user")]):
        stream_results.append(copy.copy(chunk))

    # Should have exactly 2 items: the string content, then the CreateResult
    assert len(stream_results) == 2

    # First item should be the string content
    assert isinstance(stream_results[0], str)
    assert stream_results[0] == responses[0]

    # Second item should be the CreateResult
    assert isinstance(stream_results[1], CreateResult)
    assert stream_results[1].content == responses[0]
    assert stream_results[1].finish_reason == "stop"
    assert stream_results[1].cached is True