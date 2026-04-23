def test_flush_unresolved_at_result_message():
    """Built-in tools (WebSearch) without UserMessage results get flushed at ResultMessage."""
    adapter = _adapter()
    all_responses: list[StreamBaseResponse] = []

    # 1. Init
    all_responses.extend(
        adapter.convert_message(SystemMessage(subtype="init", data={}))
    )
    # 2. Tool use (built-in tool — no MCP prefix)
    all_responses.extend(
        adapter.convert_message(
            AssistantMessage(
                content=[
                    ToolUseBlock(id="ws-1", name="WebSearch", input={"query": "test"})
                ],
                model="test",
            )
        )
    )
    # 3. No UserMessage for this tool — go straight to ResultMessage
    all_responses.extend(
        adapter.convert_message(
            ResultMessage(
                subtype="success",
                duration_ms=100,
                duration_api_ms=50,
                is_error=False,
                num_turns=1,
                session_id="s1",
            )
        )
    )

    types = [type(r).__name__ for r in all_responses]
    assert types == [
        "StreamStart",
        "StreamStartStep",
        "StreamToolInputStart",
        "StreamToolInputAvailable",
        "StreamToolOutputAvailable",  # flushed with empty output
        "StreamFinishStep",  # step closed by flush
        # Flush marks a tool_result as seen, so the thinking-only-final-turn
        # guard at ResultMessage time synthesizes a closing text delta.
        "StreamStartStep",
        "StreamTextStart",
        "StreamTextDelta",
        "StreamTextEnd",
        "StreamFinishStep",
        "StreamFinish",
    ]
    # The flushed output should be empty (no stash available)
    output_event = [
        r for r in all_responses if isinstance(r, StreamToolOutputAvailable)
    ][0]
    assert output_event.toolCallId == "ws-1"
    assert output_event.toolName == "WebSearch"
    assert output_event.output == ""