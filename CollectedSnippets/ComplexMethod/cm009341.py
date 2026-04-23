def test_tool_choice() -> None:
    """Test that tool choice is respected."""
    llm = ChatGroq(model=DEFAULT_MODEL_NAME)

    class MyTool(BaseModel):
        name: str
        age: int

    with_tool = llm.bind_tools([MyTool], tool_choice="MyTool")

    resp = with_tool.invoke("Who was the 27 year old named Erick? Use the tool.")
    assert isinstance(resp, AIMessage)
    assert resp.content == ""  # should just be tool call
    tool_calls = resp.additional_kwargs["tool_calls"]
    assert len(tool_calls) == 1
    tool_call = tool_calls[0]
    assert tool_call["function"]["name"] == "MyTool"
    assert json.loads(tool_call["function"]["arguments"]) == {
        "age": 27,
        "name": "Erick",
    }
    assert tool_call["type"] == "function"

    assert isinstance(resp.tool_calls, list)
    assert len(resp.tool_calls) == 1
    tool_call = resp.tool_calls[0]
    assert tool_call["name"] == "MyTool"
    assert tool_call["args"] == {"name": "Erick", "age": 27}