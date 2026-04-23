def test_human_in_the_loop_middleware_preserves_order_with_rejections() -> None:
    """Test that order is preserved when some interrupt tools are rejected."""
    middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "tool_b": {"allowed_decisions": ["approve", "edit", "reject"]},
            "tool_d": {"allowed_decisions": ["approve", "edit", "reject"]},
        }
    )

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

    def mock_mixed_responses(_: Any) -> dict[str, Any]:
        # Reject tool_b, approve tool_d
        return {
            "decisions": [
                {"type": "reject", "message": "Rejected tool B"},
                {"type": "approve"},
            ]
        }

    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt", side_effect=mock_mixed_responses
    ):
        result = middleware.after_model(state, Runtime())
        assert result is not None
        assert len(result["messages"]) == 2  # AI message + tool message for rejection

        updated_ai_message = result["messages"][0]
        # tool_b is still in the list (with rejection handled via tool message)
        assert len(updated_ai_message.tool_calls) == 5

        # Verify order maintained: A (auto) -> B (rejected) -> C (auto) -> D (approved) -> E (auto)
        assert updated_ai_message.tool_calls[0]["name"] == "tool_a"
        assert updated_ai_message.tool_calls[1]["name"] == "tool_b"
        assert updated_ai_message.tool_calls[2]["name"] == "tool_c"
        assert updated_ai_message.tool_calls[3]["name"] == "tool_d"
        assert updated_ai_message.tool_calls[4]["name"] == "tool_e"

        # Check rejection tool message
        tool_message = result["messages"][1]
        assert isinstance(tool_message, ToolMessage)
        assert tool_message.content == "Rejected tool B"
        assert tool_message.tool_call_id == "id_b"