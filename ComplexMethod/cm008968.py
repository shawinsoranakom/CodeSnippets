def test_human_in_the_loop_middleware_preserves_order_with_edits() -> None:
    """Test that order is preserved when interrupt tools are edited."""
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
        ],
    )
    state = AgentState[Any](messages=[HumanMessage(content="Hello"), ai_message])

    def mock_edit_responses(_: Any) -> dict[str, Any]:
        # Edit tool_b, approve tool_d
        return {
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": Action(name="tool_b", args={"val": 200}),
                },
                {"type": "approve"},
            ]
        }

    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt", side_effect=mock_edit_responses
    ):
        result = middleware.after_model(state, Runtime())
        assert result is not None

        updated_ai_message = result["messages"][0]
        assert len(updated_ai_message.tool_calls) == 4

        # Verify order: A (auto) -> B (edited) -> C (auto) -> D (approved)
        assert updated_ai_message.tool_calls[0]["name"] == "tool_a"
        assert updated_ai_message.tool_calls[0]["args"] == {"val": 1}
        assert updated_ai_message.tool_calls[1]["name"] == "tool_b"
        assert updated_ai_message.tool_calls[1]["args"] == {"val": 200}  # Edited
        assert updated_ai_message.tool_calls[1]["id"] == "id_b"  # ID preserved
        assert updated_ai_message.tool_calls[2]["name"] == "tool_c"
        assert updated_ai_message.tool_calls[2]["args"] == {"val": 3}
        assert updated_ai_message.tool_calls[3]["name"] == "tool_d"
        assert updated_ai_message.tool_calls[3]["args"] == {"val": 4}