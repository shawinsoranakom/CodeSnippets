def test_check_cache_string_json_list_deserialization_success() -> None:
    """Test _check_cache when Redis cache returns a string containing valid JSON list.
    This tests the fix for streaming results stored as JSON strings in Redis.
    """
    _, prompts, system_prompt, replay_client, _ = get_test_data()

    # Create a JSON string representing a streaming result list
    streaming_list_json = json.dumps(
        [
            "streaming chunk 1",
            {
                "content": "streaming response from json",
                "usage": {"prompt_tokens": 8, "completion_tokens": 4},
                "cached": False,
                "finish_reason": "stop",
                "logprobs": None,
                "thought": None,
            },
            "streaming chunk 2",
        ]
    )

    # Mock cache store that returns the JSON string (simulating Redis streaming)
    mock_store = MockCacheStore(return_value=cast(Any, streaming_list_json))
    cached_client = ChatCompletionCache(replay_client, mock_store)

    # Test _check_cache method directly
    messages = [system_prompt, UserMessage(content=prompts[0], source="user")]
    cached_result, cache_key = cached_client._check_cache(messages, [], None, {})  # type: ignore

    # Should successfully reconstruct the list from JSON string
    assert cached_result is not None
    assert isinstance(cached_result, list)
    assert len(cached_result) == 3
    assert cached_result[0] == "streaming chunk 1"
    assert isinstance(cached_result[1], CreateResult)
    assert cached_result[1].content == "streaming response from json"
    assert cached_result[2] == "streaming chunk 2"
    assert cache_key is not None