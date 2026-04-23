async def test_run_agent_rejects_unknown_input_fields(setup_test_data):
    """Test that run_agent returns input_validation_error for unknown input fields."""
    user = setup_test_data["user"]
    store_submission = setup_test_data["store_submission"]

    tool = RunAgentTool()
    agent_marketplace_id = f"{user.email.split('@')[0]}/{store_submission.slug}"
    session = make_session(user_id=user.id)

    # Execute with unknown input field names
    response = await tool.execute(
        user_id=user.id,
        session_id=str(uuid.uuid4()),
        tool_call_id=str(uuid.uuid4()),
        username_agent_slug=agent_marketplace_id,
        inputs={
            "unknown_field": "some value",
            "another_unknown": "another value",
        },
        dry_run=False,
        session=session,
    )

    assert response is not None
    assert hasattr(response, "output")
    assert isinstance(response.output, str)
    result_data = orjson.loads(response.output)

    # Should return input_validation_error type with unrecognized fields
    assert result_data.get("type") == "input_validation_error"
    assert "unrecognized_fields" in result_data
    assert set(result_data["unrecognized_fields"]) == {
        "another_unknown",
        "unknown_field",
    }
    assert "inputs" in result_data  # Contains the valid schema
    assert "Agent was not executed" in result_data["message"]