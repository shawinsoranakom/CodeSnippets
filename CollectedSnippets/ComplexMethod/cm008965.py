def test_human_in_the_loop_middleware_interrupt_request_structure() -> None:
    """Test that interrupt requests are structured correctly."""
    middleware = HumanInTheLoopMiddleware(
        interrupt_on={"test_tool": {"allowed_decisions": ["approve", "edit", "reject"]}},
        description_prefix="Custom prefix",
    )

    ai_message = AIMessage(
        content="I'll help you",
        tool_calls=[{"name": "test_tool", "args": {"input": "test", "location": "SF"}, "id": "1"}],
    )
    state = AgentState[Any](messages=[HumanMessage(content="Hello"), ai_message])

    captured_request = None

    def mock_capture_requests(request: Any) -> dict[str, Any]:
        nonlocal captured_request
        captured_request = request
        return {"decisions": [{"type": "approve"}]}

    with patch(
        "langchain.agents.middleware.human_in_the_loop.interrupt", side_effect=mock_capture_requests
    ):
        middleware.after_model(state, Runtime())

        assert captured_request is not None
        assert "action_requests" in captured_request
        assert "review_configs" in captured_request

        assert len(captured_request["action_requests"]) == 1
        action_request = captured_request["action_requests"][0]
        assert action_request["name"] == "test_tool"
        assert action_request["args"] == {"input": "test", "location": "SF"}
        assert "Custom prefix" in action_request["description"]
        assert "Tool: test_tool" in action_request["description"]
        assert "Args: {'input': 'test', 'location': 'SF'}" in action_request["description"]

        assert len(captured_request["review_configs"]) == 1
        review_config = captured_request["review_configs"][0]
        assert review_config["action_name"] == "test_tool"
        assert review_config["allowed_decisions"] == ["approve", "edit", "reject"]