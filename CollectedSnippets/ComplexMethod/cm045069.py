async def test_basic_workflow(mock_mem0_class: MagicMock, local_config: Mem0MemoryConfig) -> None:
    """Test basic memory operations."""
    # Setup mock
    mock_mem0 = MagicMock()
    mock_mem0_class.from_config.return_value = mock_mem0

    # Mock search results
    mock_mem0.search.return_value = [
        {
            "memory": "Paris is known for the Eiffel Tower and amazing cuisine.",
            "score": 0.95,
            "metadata": {"category": "city", "country": "France"},
        }
    ]

    memory = Mem0Memory(
        user_id=local_config.user_id,
        limit=local_config.limit,
        is_cloud=local_config.is_cloud,
        api_key=local_config.api_key,
        config=local_config.config,
    )

    # Add content to memory
    await memory.add(
        MemoryContent(
            content="Paris is known for the Eiffel Tower and amazing cuisine.",
            mime_type=MemoryMimeType.TEXT,
            metadata={"category": "city", "country": "France"},
        )
    )

    # Verify add was called correctly
    mock_mem0.add.assert_called_once()
    call_args = mock_mem0.add.call_args[0]

    # Extract content from the list of dict structure: [{'content': '...', 'role': 'user'}]
    actual_content = call_args[0][0]["content"]
    assert actual_content == "Paris is known for the Eiffel Tower and amazing cuisine."

    call_kwargs = mock_mem0.add.call_args[1]
    assert call_kwargs["metadata"] == {"category": "city", "country": "France"}

    # Query memory
    results = await memory.query("Tell me about Paris")

    # Verify search was called correctly
    mock_mem0.search.assert_called_once()
    search_args = mock_mem0.search.call_args
    assert search_args[0][0] == "Tell me about Paris"
    assert search_args[1]["user_id"] == "test-user"
    assert search_args[1]["limit"] == 3

    # Verify results
    assert len(results.results) == 1
    assert "Paris" in str(results.results[0].content)
    res_metadata = results.results[0].metadata
    assert res_metadata is not None and res_metadata.get("score") == 0.95
    assert res_metadata is not None and res_metadata.get("country") == "France"

    # Test clear (only do this once)
    await memory.clear()
    mock_mem0.delete_all.assert_called_once_with(user_id="test-user")

    # Cleanup
    await memory.close()