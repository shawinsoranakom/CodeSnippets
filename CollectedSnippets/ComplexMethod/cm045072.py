async def test_update_context(mock_mem0_class: MagicMock, local_config: Mem0MemoryConfig) -> None:
    """Test updating model context with retrieved memories."""
    # Setup mock
    mock_mem0 = MagicMock()
    mock_mem0_class.from_config.return_value = mock_mem0

    # Setup mock search results
    mock_mem0.search.return_value = [
        {"memory": "Jupiter is the largest planet in our solar system.", "score": 0.9},
        {"memory": "Jupiter has many moons, including Ganymede, Europa, and Io.", "score": 0.8},
    ]

    memory = Mem0Memory(
        user_id=local_config.user_id,
        limit=local_config.limit,
        is_cloud=local_config.is_cloud,
        api_key=local_config.api_key,
        config=local_config.config,
    )

    # Create a model context with a message
    context = BufferedChatCompletionContext(buffer_size=5)
    await context.add_message(UserMessage(content="Tell me about Jupiter", source="user"))

    # Update context with memory
    result = await memory.update_context(context)

    # Verify results
    assert len(result.memories.results) == 2
    assert "Jupiter" in str(result.memories.results[0].content)

    # Verify search was called with correct query
    mock_mem0.search.assert_called_once()
    search_args = mock_mem0.search.call_args
    assert "Jupiter" in search_args[0][0]

    # Verify context was updated with a system message
    messages = await context.get_messages()
    assert len(messages) == 2  # Original message + system message with memories

    # Verify system message content
    system_message = messages[1]
    assert isinstance(system_message, SystemMessage)
    assert "Jupiter is the largest planet" in system_message.content
    assert "Jupiter has many moons" in system_message.content

    # Cleanup
    await memory.close()