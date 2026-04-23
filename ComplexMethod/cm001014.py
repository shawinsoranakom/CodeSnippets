async def test_run_agent_missing_credentials(setup_firecrawl_test_data):
    """Test that run_agent returns setup_requirements when credentials are missing."""
    user = setup_firecrawl_test_data["user"]
    store_submission = setup_firecrawl_test_data["store_submission"]

    tool = RunAgentTool()
    agent_marketplace_id = f"{user.email.split('@')[0]}/{store_submission.slug}"
    session = make_session(user_id=user.id)

    # Execute - user doesn't have firecrawl credentials
    response = await tool.execute(
        user_id=user.id,
        session_id=str(uuid.uuid4()),
        tool_call_id=str(uuid.uuid4()),
        username_agent_slug=agent_marketplace_id,
        inputs={"url": "https://example.com"},
        dry_run=False,
        session=session,
    )

    assert response is not None
    assert hasattr(response, "output")
    assert isinstance(response.output, str)
    result_data = orjson.loads(response.output)

    # Should return setup_requirements type with missing credentials
    assert result_data.get("type") == "setup_requirements"
    assert "setup_info" in result_data
    setup_info = result_data["setup_info"]
    assert "user_readiness" in setup_info
    assert setup_info["user_readiness"]["has_all_credentials"] is False
    assert len(setup_info["user_readiness"]["missing_credentials"]) > 0