def test_redis_store_nested_model_serialization() -> None:
    """Test serialization and deserialization of nested Pydantic models."""
    from autogen_ext.cache_store.redis import RedisStore

    redis_instance = MagicMock()
    store = RedisStore[ComplexModel](redis_instance)
    test_key = "test_complex_model_key"

    # Create a complex model with nested models
    test_complex_model = ComplexModel(
        sample=SampleModel(name="nested_test", value=100),
        nested=NestedModel(id=1, data="nested_data"),
        tags=["tag1", "tag2", "tag3"],
    )

    # Test setting a complex nested model
    store.set(test_key, test_complex_model)

    # Verify the Redis instance was called with serialized data
    args, _ = redis_instance.set.call_args
    assert args[0] == test_key
    assert isinstance(args[1], bytes)

    # Verify the serialized data can be deserialized back to the original structure
    serialized_json = args[1].decode("utf-8")
    deserialized_data = json.loads(serialized_json)

    assert deserialized_data["sample"]["name"] == "nested_test"
    assert deserialized_data["sample"]["value"] == 100
    assert deserialized_data["nested"]["id"] == 1
    assert deserialized_data["nested"]["data"] == "nested_data"
    assert deserialized_data["tags"] == ["tag1", "tag2", "tag3"]

    # Test retrieving the complex nested model
    serialized_model = test_complex_model.model_dump_json().encode("utf-8")
    redis_instance.get.return_value = serialized_model

    # When we retrieve, we get the JSON data back as a dict
    retrieved_model = store.get(test_key)
    assert retrieved_model is not None
    assert isinstance(retrieved_model, dict)
    assert retrieved_model["sample"]["name"] == "nested_test"  # type: ignore
    assert retrieved_model["sample"]["value"] == 100  # type: ignore
    assert retrieved_model["nested"]["id"] == 1  # type: ignore
    assert retrieved_model["nested"]["data"] == "nested_data"  # type: ignore
    assert retrieved_model["tags"] == ["tag1", "tag2", "tag3"]