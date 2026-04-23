def test_human_in_the_loop_middleware_boolean_configs() -> None:
    """Test HITL middleware with boolean tool configs."""
    middleware = HumanInTheLoopMiddleware(interrupt_on={"test_tool": True})

    ai_message = AIMessage(
        content="I'll help you",
        tool_calls=[{"name": "test_tool", "args": {"input": "test"}, "id": "1"}],
    )
    state = AgentState[Any](messages=[HumanMessage(content="Hello"), ai_message])

    # Test accept
    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt",
        return_value={"decisions": [{"type": "approve"}]},
    ):
        result = middleware.after_model(state, Runtime())
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].tool_calls == ai_message.tool_calls

    # Test edit
    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt",
        return_value={
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": Action(
                        name="test_tool",
                        args={"input": "edited"},
                    ),
                }
            ]
        },
    ):
        result = middleware.after_model(state, Runtime())
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) == 1
        assert result["messages"][0].tool_calls[0]["args"] == {"input": "edited"}

    middleware = HumanInTheLoopMiddleware(interrupt_on={"test_tool": False})

    result = middleware.after_model(state, Runtime())
    # No interruption should occur
    assert result is None