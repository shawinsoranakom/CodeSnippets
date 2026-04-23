async def test_tool_astreaming(model: str) -> None:
    """Test that the model can stream tool calls."""
    llm = ChatOllama(model=model)
    chat_model_with_tools = llm.bind_tools([get_current_weather])

    prompt = [HumanMessage("What is the weather today in Boston?")]

    # Flags and collectors for validation
    tool_chunk_found = False
    final_tool_calls = []
    collected_tool_chunks: list[ToolCallChunk] = []

    # Stream the response and inspect the chunks
    async for chunk in chat_model_with_tools.astream(prompt):
        assert isinstance(chunk, AIMessageChunk), "Expected AIMessageChunk type"

        if chunk.tool_call_chunks:
            tool_chunk_found = True
            collected_tool_chunks.extend(chunk.tool_call_chunks)

        if chunk.tool_calls:
            final_tool_calls.extend(chunk.tool_calls)

    assert tool_chunk_found, "Tool streaming did not produce any tool_call_chunks."
    assert len(final_tool_calls) == 1, (
        f"Expected 1 final tool call, but got {len(final_tool_calls)}"
    )

    final_tool_call = final_tool_calls[0]
    assert final_tool_call["name"] == "get_current_weather"
    assert final_tool_call["args"] == {"location": "Boston"}

    assert len(collected_tool_chunks) > 0
    assert collected_tool_chunks[0]["name"] == "get_current_weather"

    # The ID should be consistent across chunks that have it
    tool_call_id = collected_tool_chunks[0].get("id")
    assert tool_call_id is not None
    assert all(
        chunk.get("id") == tool_call_id
        for chunk in collected_tool_chunks
        if chunk.get("id")
    )
    assert final_tool_call["id"] == tool_call_id