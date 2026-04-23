async def test_component_serialization(mock_memory_client_class: MagicMock) -> None:
    """Test serialization and deserialization of the component."""
    # Setup mock
    mock_client = MagicMock()
    mock_memory_client_class.return_value = mock_client

    # Create configuration
    user_id = str(uuid.uuid4())
    config = Mem0MemoryConfig(
        user_id=user_id,
        limit=5,
        is_cloud=True,
    )

    # Create memory instance
    memory = Mem0Memory(
        user_id=config.user_id,
        limit=config.limit,
        is_cloud=config.is_cloud,
        api_key=config.api_key,
        config=config.config,
    )

    # Dump config
    memory_config = memory.dump_component()

    # Verify dumped config
    assert memory_config.config["user_id"] == user_id
    assert memory_config.config["limit"] == 5
    assert memory_config.config["is_cloud"] is True

    # Load from config
    loaded_memory = Mem0Memory(
        user_id=config.user_id,
        limit=config.limit,
        is_cloud=config.is_cloud,
        api_key=config.api_key,
        config=config.config,
    )

    # Verify loaded instance
    assert isinstance(loaded_memory, Mem0Memory)
    assert loaded_memory.user_id == user_id
    assert loaded_memory.limit == 5
    assert loaded_memory.is_cloud is True
    assert loaded_memory.config is None

    # Cleanup
    await memory.close()
    await loaded_memory.close()