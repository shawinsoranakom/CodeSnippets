def test_human_in_the_loop_middleware_multiple_tools_edit_responses() -> None:
    """Test HumanInTheLoopMiddleware with multiple tools and edit responses."""
    middleware = HumanInTheLoopMiddleware(
        interrupt_on={
            "get_forecast": {"allowed_decisions": ["approve", "edit", "reject"]},
            "get_temperature": {"allowed_decisions": ["approve", "edit", "reject"]},
        }
    )

    ai_message = AIMessage(
        content="I'll help you with weather",
        tool_calls=[
            {"name": "get_forecast", "args": {"location": "San Francisco"}, "id": "1"},
            {"name": "get_temperature", "args": {"location": "San Francisco"}, "id": "2"},
        ],
    )
    state = AgentState[Any](messages=[HumanMessage(content="What's the weather?"), ai_message])

    def mock_edit_responses(_: Any) -> dict[str, Any]:
        return {
            "decisions": [
                {
                    "type": "edit",
                    "edited_action": Action(
                        name="get_forecast",
                        args={"location": "New York"},
                    ),
                },
                {
                    "type": "edit",
                    "edited_action": Action(
                        name="get_temperature",
                        args={"location": "New York"},
                    ),
                },
            ]
        }

    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt", side_effect=mock_edit_responses
    ):
        result = middleware.after_model(state, Runtime())
        assert result is not None
        assert "messages" in result
        assert len(result["messages"]) == 1

        updated_ai_message = result["messages"][0]
        assert updated_ai_message.tool_calls[0]["args"] == {"location": "New York"}
        assert updated_ai_message.tool_calls[0]["id"] == "1"  # ID preserved
        assert updated_ai_message.tool_calls[1]["args"] == {"location": "New York"}
        assert updated_ai_message.tool_calls[1]["id"] == "2"