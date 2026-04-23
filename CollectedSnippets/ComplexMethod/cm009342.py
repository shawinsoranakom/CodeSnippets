def test_streaming_tool_call() -> None:
    """Test that tool choice is respected."""
    llm = ChatGroq(model=DEFAULT_MODEL_NAME)

    class MyTool(BaseModel):
        name: str
        age: int

    with_tool = llm.bind_tools([MyTool], tool_choice="MyTool")

    resp = with_tool.stream("Who was the 27 year old named Erick?")
    additional_kwargs = None
    for chunk in resp:
        assert isinstance(chunk, AIMessageChunk)
        assert chunk.content == ""  # should just be tool call
        additional_kwargs = chunk.additional_kwargs

    assert additional_kwargs is not None
    tool_calls = additional_kwargs["tool_calls"]
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["function"]["name"] == "MyTool"
    assert json.loads(tool_call["function"]["arguments"]) == {
        "age": 27,
        "name": "Erick",
    }
    assert tool_call["type"] == "function"

    assert isinstance(chunk, AIMessageChunk)
    assert isinstance(chunk.tool_call_chunks, list)
    assert len(chunk.tool_call_chunks) == 1
    tool_call_chunk = chunk.tool_call_chunks[0]
    assert tool_call_chunk["name"] == "MyTool"
    assert isinstance(tool_call_chunk["args"], str)
    assert json.loads(tool_call_chunk["args"]) == {"name": "Erick", "age": 27}