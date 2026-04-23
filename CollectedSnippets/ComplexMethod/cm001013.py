async def test_run_agent_shows_available_inputs_when_none_provided(setup_test_data):
    """Test that run_agent returns available inputs when called without inputs or use_defaults."""
    user = setup_test_data["user"]
    store_submission = setup_test_data["store_submission"]

    tool = RunAgentTool()
    agent_marketplace_id = f"{user.email.split('@')[0]}/{store_submission.slug}"
    session = make_session(user_id=user.id)

    # Execute without inputs and without use_defaults
    response = await tool.execute(
        user_id=user.id,
        session_id=str(uuid.uuid4()),
        tool_call_id=str(uuid.uuid4()),
        username_agent_slug=agent_marketplace_id,
        inputs={},
        use_defaults=False,
        dry_run=False,
        session=session,
    )

    assert response is not None
    assert hasattr(response, "output")
    assert isinstance(response.output, str)
    result_data = orjson.loads(response.output)

    # Should return agent_details type showing available inputs
    assert result_data.get("type") == "agent_details"
    assert "agent" in result_data
    assert "message" in result_data
    # Message should mention inputs
    assert "inputs" in result_data["message"].lower()