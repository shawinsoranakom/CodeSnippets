def test_redis_store_mixed_list_streaming_scenario() -> None:
    """Test serialization of mixed lists (strings + CreateResult) for streaming cache scenario."""
    from autogen_ext.cache_store.redis import RedisStore

    redis_instance = MagicMock()
    store = RedisStore[List[Union[str, CreateResult]]](redis_instance)
    test_key = "test_mixed_streaming_list_key"

    # Create a mixed list simulating a streaming response
    usage = RequestUsage(prompt_tokens=15, completion_tokens=30)
    mixed_list: List[Union[str, CreateResult]] = [
        "The",
        " capital",
        " of",
        " France",
        " is",
        " Paris",
        ".",
        CreateResult(content="The capital of France is Paris.", usage=usage, finish_reason="stop", cached=False),
    ]

    # Test setting the mixed list
    store.set(test_key, mixed_list)

    # Verify Redis was called with JSON-serialized data
    args, _ = redis_instance.set.call_args
    assert args[0] == test_key
    assert isinstance(args[1], bytes)

    # Verify the serialized data structure
    serialized_json = args[1].decode("utf-8")
    deserialized_data = json.loads(serialized_json)

    assert isinstance(deserialized_data, list)
    # Type narrowing: after isinstance check, deserialized_data is known to be a list
    deserialized_list: List[Union[str, Dict[str, Union[str, int]]]] = deserialized_data  # Now properly typed as list
    assert len(deserialized_list) == 8  # 7 strings + 1 CreateResult

    # First 7 items should be strings
    for i in range(7):
        assert isinstance(deserialized_list[i], str)

    # Last item should be the serialized CreateResult (as dict)
    assert isinstance(deserialized_list[7], dict)
    assert deserialized_list[7]["content"] == "The capital of France is Paris."
    assert deserialized_list[7]["finish_reason"] == "stop"
    assert deserialized_data[7]["usage"]["prompt_tokens"] == 15
    assert deserialized_data[7]["usage"]["completion_tokens"] == 30

    # Test retrieving the mixed list
    redis_instance.get.return_value = args[1]  # Return the serialized data
    retrieved_list = store.get(test_key)

    assert retrieved_list is not None
    assert isinstance(retrieved_list, list)
    assert len(retrieved_list) == 8

    # First 7 items should still be strings
    for i in range(7):
        assert isinstance(retrieved_list[i], str)
        assert retrieved_list[i] == mixed_list[i]

    # Last item should be a dict (CreateResult deserialized from JSON)
    assert isinstance(retrieved_list[7], dict)
    assert retrieved_list[7]["content"] == "The capital of France is Paris."  # type: ignore
    assert retrieved_list[7]["cached"] is False