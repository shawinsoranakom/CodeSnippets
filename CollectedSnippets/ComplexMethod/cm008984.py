def test_respects_keep_last_tool_results() -> None:
    conversation: list[AIMessage | ToolMessage] = []
    edits = [
        ("call-a", "tool-output-a" * 5),
        ("call-b", "tool-output-b" * 5),
        ("call-c", "tool-output-c" * 5),
    ]

    for call_id, text in edits:
        conversation.extend(
            (
                AIMessage(
                    content="",
                    tool_calls=[{"id": call_id, "name": "tool", "args": {"input": call_id}}],
                ),
                ToolMessage(content=text, tool_call_id=call_id),
            )
        )

    _state, request = _make_state_and_request(conversation)

    middleware = ContextEditingMiddleware(
        edits=[
            ClearToolUsesEdit(
                trigger=50,
                keep=1,
                placeholder="[cleared]",
            )
        ],
        token_count_method="model",  # noqa: S106
    )

    modified_request = None

    def mock_handler(req: ModelRequest) -> ModelResponse:
        nonlocal modified_request
        modified_request = req
        return ModelResponse(result=[AIMessage(content="mock response")])

    # Call wrap_model_call which creates a new request with edits
    middleware.wrap_model_call(request, mock_handler)

    assert modified_request is not None
    cleared_messages = [
        msg
        for msg in modified_request.messages
        if isinstance(msg, ToolMessage) and msg.content == "[cleared]"
    ]

    assert len(cleared_messages) == 2
    assert isinstance(modified_request.messages[-1], ToolMessage)
    assert modified_request.messages[-1].content != "[cleared]"