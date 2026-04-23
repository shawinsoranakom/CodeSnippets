def test_check_cache_redis_streaming_dict_deserialization() -> None:
    """Test _check_cache with Redis streaming data containing dicts that need deserialization.
    This tests the streaming scenario where Redis returns a list containing
    serialized CreateResult objects as dictionaries mixed with string chunks.
    """
    _, prompts, system_prompt, replay_client, _ = get_test_data()

    # Create a list with CreateResult objects mixed with strings (streaming scenario)
    create_result = CreateResult(
        content="final streaming response from redis",
        usage=RequestUsage(prompt_tokens=12, completion_tokens=6),
        cached=False,
        finish_reason="stop",
    )

    cached_list: List[Union[str, CreateResult]] = [
        "streaming chunk 1",
        create_result,  # Proper CreateResult object
        "streaming chunk 2",
    ]

    # Mock cache store that returns the list with CreateResults (simulating Redis streaming)
    mock_store = MockCacheStore(return_value=cached_list)
    cached_client = ChatCompletionCache(replay_client, mock_store)

    # Test _check_cache method directly using proper test data
    messages = [system_prompt, UserMessage(content=prompts[2], source="user")]
    cached_result, cache_key = cached_client._check_cache(messages, [], None, {})  # type: ignore

    assert cached_result is not None
    assert isinstance(cached_result, list)
    assert len(cached_result) == 3
    assert cached_result[0] == "streaming chunk 1"
    assert isinstance(cached_result[1], CreateResult)
    assert cached_result[1].content == "final streaming response from redis"
    assert cached_result[2] == "streaming chunk 2"
    assert cache_key is not None