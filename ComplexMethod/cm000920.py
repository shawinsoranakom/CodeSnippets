def test_parallel_tool_calls_not_flushed_prematurely():
    """Parallel tool calls should NOT be flushed when the next AssistantMessage
    only contains ToolUseBlocks (parallel continuation)."""
    adapter = SDKResponseAdapter()

    # Init
    adapter.convert_message(SystemMessage(subtype="init", data={}))

    # First AssistantMessage: tool call #1
    msg1 = AssistantMessage(
        content=[ToolUseBlock(id="t1", name="WebSearch", input={"q": "foo"})],
        model="test",
    )
    r1 = adapter.convert_message(msg1)
    assert any(isinstance(r, StreamToolInputAvailable) for r in r1)
    assert adapter.has_unresolved_tool_calls

    # Second AssistantMessage: tool call #2 (parallel continuation)
    msg2 = AssistantMessage(
        content=[ToolUseBlock(id="t2", name="WebSearch", input={"q": "bar"})],
        model="test",
    )
    r2 = adapter.convert_message(msg2)

    # No flush should have happened — t1 should NOT have StreamToolOutputAvailable
    output_events = [r for r in r2 if isinstance(r, StreamToolOutputAvailable)]
    assert len(output_events) == 0, (
        f"Tool-only AssistantMessage should not flush prior tools, "
        f"but got {len(output_events)} output events"
    )

    # Both t1 and t2 should still be unresolved
    assert "t1" not in adapter.resolved_tool_calls
    assert "t2" not in adapter.resolved_tool_calls