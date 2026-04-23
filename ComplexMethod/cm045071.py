async def test_metadata_handling(mock_mem0_class: MagicMock, local_config: Mem0MemoryConfig) -> None:
    """Test metadata handling."""
    # Setup mock
    mock_mem0 = MagicMock()
    mock_mem0_class.from_config.return_value = mock_mem0

    # Setup mock search results with rich metadata
    mock_mem0.search.return_value = [
        {
            "memory": "Test content with metadata",
            "score": 0.9,
            "metadata": {"test_category": "test", "test_priority": 1, "test_weight": 0.5, "test_verified": True},
            "created_at": "2023-01-01T12:00:00",
            "updated_at": "2023-01-02T12:00:00",
            "categories": ["test", "example"],
        }
    ]

    memory = Mem0Memory(
        user_id=local_config.user_id,
        limit=local_config.limit,
        is_cloud=local_config.is_cloud,
        api_key=local_config.api_key,
        config=local_config.config,
    )

    # Add content with metadata
    test_content = "Test content with specific metadata"
    content = MemoryContent(
        content=test_content,
        mime_type=MemoryMimeType.TEXT,
        metadata={"test_category": "test", "test_priority": 1, "test_weight": 0.5, "test_verified": True},
    )
    await memory.add(content)

    # Verify metadata was passed correctly
    add_kwargs = mock_mem0.add.call_args[1]
    assert add_kwargs["metadata"]["test_category"] == "test"
    assert add_kwargs["metadata"]["test_priority"] == 1
    assert add_kwargs["metadata"]["test_weight"] == 0.5
    assert add_kwargs["metadata"]["test_verified"] is True

    # Query and check returned metadata
    results = await memory.query(test_content)
    assert len(results.results) == 1
    result = results.results[0]

    # Verify metadata in results
    assert result.metadata is not None and result.metadata.get("test_category") == "test"
    assert result.metadata is not None and result.metadata.get("test_priority") == 1
    assert result.metadata is not None and isinstance(result.metadata.get("test_weight"), float)
    assert result.metadata is not None and result.metadata.get("test_verified") is True
    assert result.metadata is not None and "created_at" in result.metadata
    assert result.metadata is not None and "updated_at" in result.metadata
    assert result.metadata is not None and result.metadata.get("categories") == ["test", "example"]

    # Cleanup
    await memory.close()