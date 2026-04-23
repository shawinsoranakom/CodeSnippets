def test_clear_tool_outputs_and_inputs() -> None:
    tool_call_id = "call-2"
    ai_message = AIMessage(
        content=[
            {"type": "tool_call", "id": tool_call_id, "name": "search", "args": {"query": "foo"}}
        ],
        tool_calls=[{"id": tool_call_id, "name": "search", "args": {"query": "foo"}}],
    )
    tool_message = ToolMessage(content="x" * 200, tool_call_id=tool_call_id)

    _state, request = _make_state_and_request([ai_message, tool_message])

    edit = ClearToolUsesEdit(
        trigger=50,
        clear_at_least=10,
        clear_tool_inputs=True,
        keep=0,
        placeholder="[cleared output]",
    )
    middleware = ContextEditingMiddleware(edits=[edit])

    modified_request = None

    def mock_handler(req: ModelRequest) -> ModelResponse:
        nonlocal modified_request
        modified_request = req
        return ModelResponse(result=[AIMessage(content="mock response")])

    # Call wrap_model_call which creates a new request with edits
    middleware.wrap_model_call(request, mock_handler)

    assert modified_request is not None
    cleared_ai = modified_request.messages[0]
    cleared_tool = modified_request.messages[1]

    assert isinstance(cleared_tool, ToolMessage)
    assert cleared_tool.content == "[cleared output]"
    assert cleared_tool.response_metadata["context_editing"]["cleared"] is True

    assert isinstance(cleared_ai, AIMessage)
    assert cleared_ai.tool_calls[0]["args"] == {}
    context_meta = cleared_ai.response_metadata.get("context_editing")
    assert context_meta is not None
    assert context_meta["cleared_tool_inputs"] == [tool_call_id]

    # Original request should be unchanged
    request_ai_message = request.messages[0]
    assert isinstance(request_ai_message, AIMessage)
    assert request_ai_message.tool_calls[0]["args"] == {"query": "foo"}
    assert request.messages[1].content == "x" * 200