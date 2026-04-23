async def test_local_config_with_memory_operations(
    mock_mem0_class: MagicMock,
    full_local_config: Dict[str, Any],  # full_local_config fixture provides the mock config
) -> None:
    """Test memory operations with local configuration."""
    # Setup mock for the instance that will be created by Mem0Memory
    mock_mem0_instance = MagicMock()
    mock_mem0_class.from_config.return_value = mock_mem0_instance

    # Mock search results from the mem0 instance
    mock_mem0_instance.search.return_value = [
        {
            "memory": "Test local config memory content",
            "score": 0.92,
            "metadata": {"config_type": "local", "test_case": "advanced"},
        }
    ]

    # Initialize Mem0Memory with is_cloud=False and the full_local_config
    memory = Mem0Memory(user_id="test-local-config-user", limit=10, is_cloud=False, config=full_local_config)

    # Verify that mem0.Memory.from_config was called with the provided config
    mock_mem0_class.from_config.assert_called_once_with(config_dict=full_local_config)

    # Add memory content
    test_content_str = "Testing local configuration memory operations"
    await memory.add(
        MemoryContent(
            content=test_content_str,
            mime_type=MemoryMimeType.TEXT,
            metadata={"config_type": "local", "test_case": "advanced"},
        )
    )

    # Verify add was called on the mock_mem0_instance
    mock_mem0_instance.add.assert_called_once()

    # Query memory
    results = await memory.query("local configuration test")

    # Verify search was called on the mock_mem0_instance
    mock_mem0_instance.search.assert_called_once_with(
        "local configuration test", user_id="test-local-config-user", limit=10
    )

    # Verify results
    assert len(results.results) == 1
    assert "Test local config memory content" in str(results.results[0].content)
    res_metadata = results.results[0].metadata
    assert res_metadata is not None and res_metadata.get("score") == 0.92
    assert res_metadata is not None and res_metadata.get("config_type") == "local"

    # Test serialization with local config
    memory_config = memory.dump_component()

    # Verify serialized config
    assert memory_config.config["user_id"] == "test-local-config-user"
    assert memory_config.config["is_cloud"] is False
    assert "config" in memory_config.config
    assert memory_config.config["config"]["history_db_path"] == ":memory:"

    # Test clear
    await memory.clear()
    mock_mem0_instance.delete_all.assert_called_once_with(user_id="test-local-config-user")

    # Cleanup
    await memory.close()