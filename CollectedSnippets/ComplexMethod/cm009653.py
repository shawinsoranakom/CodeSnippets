def test_message_chunk_to_message() -> None:
    assert message_chunk_to_message(
        AIMessageChunk(content="I am", additional_kwargs={"foo": "bar"})
    ) == AIMessage(content="I am", additional_kwargs={"foo": "bar"})
    assert message_chunk_to_message(HumanMessageChunk(content="I am")) == HumanMessage(
        content="I am"
    )
    assert message_chunk_to_message(
        ChatMessageChunk(role="User", content="I am")
    ) == ChatMessage(role="User", content="I am")
    assert message_chunk_to_message(
        FunctionMessageChunk(name="hello", content="I am")
    ) == FunctionMessage(name="hello", content="I am")

    chunk = AIMessageChunk(
        content="I am",
        tool_call_chunks=[
            create_tool_call_chunk(name="tool1", args='{"a": 1}', id="1", index=0),
            create_tool_call_chunk(name="tool2", args='{"b": ', id="2", index=0),
            create_tool_call_chunk(name="tool3", args=None, id="3", index=0),
            create_tool_call_chunk(name="tool4", args="abc", id="4", index=0),
        ],
    )
    expected = AIMessage(
        content="I am",
        tool_calls=[
            create_tool_call(name="tool1", args={"a": 1}, id="1"),
            create_tool_call(name="tool2", args={}, id="2"),
            create_tool_call(name="tool3", args={}, id="3"),
        ],
        invalid_tool_calls=[
            create_invalid_tool_call(name="tool4", args="abc", id="4", error=None),
        ],
    )
    assert message_chunk_to_message(chunk) == expected
    assert AIMessage(**expected.model_dump()) == expected
    assert AIMessageChunk(**chunk.model_dump()) == chunk