def test_human_in_the_loop_middleware_preserves_tool_call_order() -> None:
    """Test that middleware preserves the original order of tool calls.

    This test verifies that when mixing auto-approved and interrupt tools,
    the final tool call order matches the original order from the AI message.
    """
    middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "tool_b": {"allowed_decisions": ["approve", "edit", "reject"]},
            "tool_d": {"allowed_decisions": ["approve", "edit", "reject"]},
        }
    )

    # Create AI message with interleaved auto-approved and interrupt tools
    # Order: auto (A) -> interrupt (B) -> auto (C) -> interrupt (D) -> auto (E)
    ai_message = AIMessage(
        content="Processing multiple tools",
        tool_calls=[
            {"name": "tool_a", "args": {"val": 1}, "id": "id_a"},
            {"name": "tool_b", "args": {"val": 2}, "id": "id_b"},
            {"name": "tool_c", "args": {"val": 3}, "id": "id_c"},
            {"name": "tool_d", "args": {"val": 4}, "id": "id_d"},
            {"name": "tool_e", "args": {"val": 5}, "id": "id_e"},
        ],
    )
    state = AgentState[Any](messages=[HumanMessage(content="Hello"), ai_message])

    def mock_approve_all(_: Any) -> dict[str, Any]:
        # Approve both interrupt tools (B and D)
        return {"decisions": [{"type": "approve"}, {"type": "approve"}]}

    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt", side_effect=mock_approve_all
    ):
        result = middleware.after_model(state, Runtime())
        assert result is not None
        assert "messages" in result

        updated_ai_message = result["messages"][0]
        assert len(updated_ai_message.tool_calls) == 5

        # Verify original order is preserved: A -> B -> C -> D -> E
        assert updated_ai_message.tool_calls[0]["name"] == "tool_a"
        assert updated_ai_message.tool_calls[0]["id"] == "id_a"
        assert updated_ai_message.tool_calls[1]["name"] == "tool_b"
        assert updated_ai_message.tool_calls[1]["id"] == "id_b"
        assert updated_ai_message.tool_calls[2]["name"] == "tool_c"
        assert updated_ai_message.tool_calls[2]["id"] == "id_c"
        assert updated_ai_message.tool_calls[3]["name"] == "tool_d"
        assert updated_ai_message.tool_calls[3]["id"] == "id_d"
        assert updated_ai_message.tool_calls[4]["name"] == "tool_e"
        assert updated_ai_message.tool_calls[4]["id"] == "id_e"