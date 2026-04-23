async def test_basic_workflow_with_cloud(mock_memory_client_class: MagicMock, cloud_config: Mem0MemoryConfig) -> None:
    """Test basic memory operations with cloud client (mocked instead of real API)."""
    # Setup mock
    mock_client = MagicMock()
    mock_memory_client_class.return_value = mock_client

    # Mock search results
    mock_client.search.return_value = [
        {
            "memory": "Test memory content for cloud",
            "score": 0.98,
            "metadata": {"test": True, "source": "cloud"},
        }
    ]

    memory = Mem0Memory(
        user_id=cloud_config.user_id,
        limit=cloud_config.limit,
        is_cloud=cloud_config.is_cloud,
        api_key=cloud_config.api_key,
        config=cloud_config.config,
    )

    # Generate a unique test content string
    test_content = f"Test memory content {uuid.uuid4()}"

    # Add content to memory
    await memory.add(
        MemoryContent(
            content=test_content,
            mime_type=MemoryMimeType.TEXT,
            metadata={"test": True, "timestamp": datetime.now().isoformat()},
        )
    )

    # Verify add was called correctly
    mock_client.add.assert_called_once()
    call_args = mock_client.add.call_args

    # Extract content from list of dict structure: [{'content': '...', 'role': 'user'}]
    actual_content = call_args[0][0][0]["content"]  # call_args[0][0] gets the first positional arg (the list)
    assert test_content in actual_content

    assert call_args[1]["user_id"] == cloud_config.user_id
    assert call_args[1]["metadata"]["test"] is True

    # Query memory
    results = await memory.query(test_content)

    # Verify search was called correctly
    mock_client.search.assert_called_once()
    search_args = mock_client.search.call_args
    assert test_content in search_args[0][0]
    assert search_args[1]["user_id"] == cloud_config.user_id

    # Verify results
    assert len(results.results) == 1
    assert "Test memory content for cloud" in str(results.results[0].content)
    assert results.results[0].metadata is not None
    assert results.results[0].metadata.get("score") == 0.98

    # Test clear
    await memory.clear()
    mock_client.delete_all.assert_called_once_with(user_id=cloud_config.user_id)

    # Cleanup
    await memory.close()