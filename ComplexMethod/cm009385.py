def test_tool_choice_bool(strict: bool | None) -> None:  # noqa: FBT001
    """Test that tool choice is respected with different strict values."""
    llm = ChatFireworks(model="accounts/fireworks/models/kimi-k2-instruct-0905")

    class MyTool(BaseModel):
        name: str
        age: int

    kwargs = {"tool_choice": True}
    if strict is not None:
        kwargs["strict"] = strict
    with_tool = llm.bind_tools([MyTool], **kwargs)

    # Verify that strict is correctly set in the tool definition
    assert hasattr(with_tool, "kwargs")
    tools = with_tool.kwargs.get("tools", [])
    assert len(tools) == 1
    tool_def = tools[0]
    assert "function" in tool_def
    if strict is None:
        assert "strict" not in tool_def["function"]
    else:
        assert tool_def["function"].get("strict") is strict

    resp = with_tool.invoke("Who was the 27 year old named Erick?")
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