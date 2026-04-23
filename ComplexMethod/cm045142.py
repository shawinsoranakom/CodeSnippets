def test_check_cache_list_reconstruction_success() -> None:
    """Test _check_cache successfully reconstructs CreateResult objects from dicts in a list.
    This tests the line: reconstructed_list.append(CreateResult.model_validate(item))
    """
    _, prompts, system_prompt, replay_client, _ = get_test_data()

    # Create a list with valid dicts that can be reconstructed
    valid_dict1 = {
        "content": "first result",
        "usage": {"prompt_tokens": 8, "completion_tokens": 3},
        "cached": False,
        "finish_reason": "stop",
    }
    valid_dict2 = {
        "content": "second result",
        "usage": {"prompt_tokens": 12, "completion_tokens": 7},
        "cached": False,
        "finish_reason": "stop",
    }

    cached_list = [
        "streaming chunk 1",
        valid_dict1,
        "streaming chunk 2",
        valid_dict2,
    ]

    # Create a MockCacheStore that returns the list with dicts
    mock_store = MockCacheStore(return_value=cast(Any, cached_list))
    cached_client = ChatCompletionCache(replay_client, mock_store)

    # Test _check_cache method
    messages = [system_prompt, UserMessage(content=prompts[0], source="user")]
    cached_result, cache_key = cached_client._check_cache(messages, [], None, {})  # type: ignore

    # Should successfully reconstruct the list with CreateResult objects
    assert cached_result is not None
    assert isinstance(cached_result, list)
    assert len(cached_result) == 4
    assert cached_result[0] == "streaming chunk 1"
    assert isinstance(cached_result[1], CreateResult)
    assert cached_result[1].content == "first result"
    assert cached_result[2] == "streaming chunk 2"
    assert isinstance(cached_result[3], CreateResult)
    assert cached_result[3].content == "second result"
    assert cache_key is not None