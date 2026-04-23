def test_redis_store_list_with_create_results_only() -> None:
    """Test serialization of lists containing only CreateResult objects."""
    from autogen_ext.cache_store.redis import RedisStore

    redis_instance = MagicMock()
    store = RedisStore[List[Union[str, CreateResult]]](redis_instance)
    test_key = "test_create_result_list_key"

    # Create a list with only CreateResult objects
    usage = RequestUsage(prompt_tokens=10, completion_tokens=20)
    create_result_list: List[Union[str, CreateResult]] = [
        CreateResult(content="First response", usage=usage, finish_reason="stop", cached=False),
        CreateResult(content="Second response", usage=usage, finish_reason="stop", cached=False),
    ]

    # Test setting the list
    store.set(test_key, create_result_list)

    # Verify Redis was called with JSON-serialized data
    args, _ = redis_instance.set.call_args
    assert args[0] == test_key
    assert isinstance(args[1], bytes)

    # Verify the serialized data structure
    serialized_json = args[1].decode("utf-8")
    deserialized_data = json.loads(serialized_json)

    assert isinstance(deserialized_data, list)
    # Type narrowing: after isinstance check, deserialized_data is known to be a list
    deserialized_list: List[Dict[str, Union[str, int]]] = deserialized_data  # Now properly typed as list
    assert len(deserialized_list) == 2
    assert deserialized_list[0]["content"] == "First response"
    assert deserialized_list[1]["content"] == "Second response"
    assert deserialized_list[0]["finish_reason"] == "stop"

    # Test retrieving the list
    redis_instance.get.return_value = args[1]  # Return the serialized data
    retrieved_list = store.get(test_key)

    assert retrieved_list is not None
    assert isinstance(retrieved_list, list)
    assert len(retrieved_list) == 2

    # The retrieved items should be dicts (as Redis returns JSON-parsed objects)
    assert isinstance(retrieved_list[0], dict)
    assert isinstance(retrieved_list[1], dict)
    assert retrieved_list[0]["content"] == "First response"  # type: ignore
    assert retrieved_list[1]["content"] == "Second response"