async def test_update_context(semantic_memory: RedisMemory) -> None:
    """Test updating model context with retrieved memories."""
    await semantic_memory.clear()

    # Add content to memory
    await semantic_memory.add(
        MemoryContent(
            content="Canada is the second largest country in the world.",
            mime_type=MemoryMimeType.TEXT,
            metadata={"category": "geography"},
        )
    )

    # Create a model context with a message
    context = BufferedChatCompletionContext(buffer_size=5)
    await context.add_message(UserMessage(content="Tell me about Canada", source="user"))

    # Update context with memory
    result = await semantic_memory.update_context(context)

    # Verify results
    assert len(result.memories.results) > 0
    assert any("Canada" in str(r.content) for r in result.memories.results)

    # Verify context was updated
    messages = await context.get_messages()
    assert len(messages) > 1  # Should have the original message plus the memory content

    await semantic_memory.clear()

    await semantic_memory.add(
        MemoryContent(
            content="Napoleon was Emporor of France from 18 May 1804 to 6 April 1814.",
            mime_type=MemoryMimeType.TEXT,
            metadata={},
        )
    )
    await semantic_memory.add(
        MemoryContent(
            content="Napoleon was also Emporor during his second reign from 20 March 1815 to 22 June 1815.",
            mime_type=MemoryMimeType.TEXT,
            metadata={},
        )
    )

    context = BufferedChatCompletionContext(
        buffer_size=5,
        initial_messages=[
            UserMessage(content="Can you tell me about the reign of Emperor Napoleon?", source="user"),
        ],
    )

    updated_context = await semantic_memory.update_context(context)
    assert updated_context is not None
    assert updated_context.memories is not None
    assert updated_context.memories.results is not None
    assert len(updated_context.memories.results) == 2
    assert (
        updated_context.memories.results[0].content
        == "Napoleon was Emporor of France from 18 May 1804 to 6 April 1814."
    )
    assert (
        updated_context.memories.results[1].content
        == "Napoleon was also Emporor during his second reign from 20 March 1815 to 22 June 1815."
    )