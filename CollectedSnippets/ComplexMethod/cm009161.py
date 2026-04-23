def test_tool_use() -> None:
    llm = ChatOpenAI(model="gpt-5-nano", temperature=0)
    llm_with_tool = llm.bind_tools(tools=[GenerateUsername], tool_choice=True)
    msgs: list = [HumanMessage("Sally has green hair, what would her username be?")]
    ai_msg = llm_with_tool.invoke(msgs)

    assert isinstance(ai_msg, AIMessage)
    assert isinstance(ai_msg.tool_calls, list)
    assert len(ai_msg.tool_calls) == 1
    tool_call = ai_msg.tool_calls[0]
    assert "args" in tool_call

    tool_msg = ToolMessage("sally_green_hair", tool_call_id=ai_msg.tool_calls[0]["id"])
    msgs.extend([ai_msg, tool_msg])
    llm_with_tool.invoke(msgs)

    # Test streaming
    ai_messages = llm_with_tool.stream(msgs)
    first = True
    for message in ai_messages:
        if first:
            gathered = message
            first = False
        else:
            gathered = gathered + message  # type: ignore
    assert isinstance(gathered, AIMessageChunk)
    assert isinstance(gathered.tool_call_chunks, list)
    assert len(gathered.tool_call_chunks) == 1
    tool_call_chunk = gathered.tool_call_chunks[0]
    assert "args" in tool_call_chunk
    assert gathered.content_blocks == gathered.tool_calls

    streaming_tool_msg = ToolMessage(
        "sally_green_hair", tool_call_id=gathered.tool_calls[0]["id"]
    )
    msgs.extend([gathered, streaming_tool_msg])
    llm_with_tool.invoke(msgs)