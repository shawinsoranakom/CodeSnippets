def test_redis_store_serialization() -> None:
    from autogen_ext.cache_store.redis import RedisStore

    redis_instance = MagicMock()
    store = RedisStore[SampleModel](redis_instance)
    test_key = "test_model_key"
    test_model = SampleModel(name="test", value=42)

    # Test setting a Pydantic model
    store.set(test_key, test_model)

    # The Redis instance should be called with the serialized model
    args, _ = redis_instance.set.call_args
    assert args[0] == test_key
    assert isinstance(args[1], bytes)

    # Test retrieving a serialized model
    serialized_model = test_model.model_dump_json().encode("utf-8")
    redis_instance.get.return_value = serialized_model

    # When we retrieve, we get the JSON data back as a dict
    retrieved_model = store.get(test_key)
    assert retrieved_model is not None
    # The retrieved model should be a dict with the original data.
    assert isinstance(retrieved_model, dict)
    assert retrieved_model["name"] == "test"  # type: ignore
    assert retrieved_model["value"] == 42  # type: ignore

    # Test handling non-existent keys
    redis_instance.get.return_value = None
    assert store.get("non_existent_key") is None

    # Test fallback for non-model values
    redis_instance.get.return_value = b"simple string"
    simple_value = store.get("string_key")
    # Use cast to avoid type checking errors
    assert cast(str, simple_value) == "simple string"

    # Test error handling
    redis_instance.get.return_value = b"invalid json {["
    # Use cast to avoid type checking errors
    assert cast(str, store.get("invalid_json_key")) == "invalid json {["

    # Test exception during get - reset side_effect first
    redis_instance.get.side_effect = None
    redis_instance.get.side_effect = redis.RedisError("Redis error")
    assert store.get("error_key", default=SampleModel(name="default", value=0)) == SampleModel(name="default", value=0)

    # Test exception during set
    redis_instance.set.side_effect = redis.RedisError("Redis error")
    try:
        # This should not raise an exception due to our try/except block
        store.set("error_key", test_model)
    except Exception:
        pytest.fail("set() method didn't handle the exception properly")