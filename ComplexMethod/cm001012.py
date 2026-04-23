async def test_run_agent_with_llm_credentials(setup_llm_test_data):
    """Test that run_agent works with an agent requiring LLM credentials"""
    # Use test data from fixture
    user = setup_llm_test_data["user"]
    graph = setup_llm_test_data["graph"]
    store_submission = setup_llm_test_data["store_submission"]

    # Create the tool instance
    tool = RunAgentTool()

    # Build the proper marketplace agent_id format
    agent_marketplace_id = f"{user.email.split('@')[0]}/{store_submission.slug}"

    # Build the session
    session = make_session(user_id=user.id)

    # Execute the tool with a prompt for the LLM
    response = await tool.execute(
        user_id=user.id,
        session_id=str(uuid.uuid4()),
        tool_call_id=str(uuid.uuid4()),
        username_agent_slug=agent_marketplace_id,
        inputs={"user_prompt": "What is 2+2?"},
        dry_run=False,
        session=session,
    )

    # Verify the response
    assert response is not None
    assert hasattr(response, "output")

    # Parse the result JSON to verify the execution started

    assert isinstance(response.output, str)
    result_data = orjson.loads(response.output)

    # Should successfully start execution since credentials are available
    assert "execution_id" in result_data
    assert "graph_id" in result_data
    assert result_data["graph_id"] == graph.id
    assert "graph_name" in result_data
    assert result_data["graph_name"] == "LLM Test Agent"