def test_ls_agent_type_is_overridable() -> None:
    """Test that ls_agent_type can be overridden via configurable in invoke config."""
    # Create a mock client to capture what gets sent to LangSmith
    mock_session = MagicMock()
    mock_client = Client(session=mock_session, api_key="test", auto_batch_tracing=False)

    agent = create_agent(
        model=FakeToolCallingModel(tool_calls=[[], []]),
        tools=[],
        system_prompt="You are a helpful assistant.",
    )

    # Use tracing_context to enable tracing with the mock client
    with tracing_context(client=mock_client, enabled=True):
        agent.invoke(
            {"messages": [HumanMessage("hi?")]},
            config={"configurable": {"ls_agent_type": "subagent", "custom_key": "custom_value"}},
        )

    # Verify that ls_agent_type is overridden and configurable is merged in the tracer metadata
    posts = []
    for call in mock_session.request.mock_calls:
        if call.args and call.args[0] == "POST":
            body = json.loads(call.kwargs["data"])
            if "post" in body:
                posts.extend(body["post"])
            else:
                posts.append(body)

    assert len(posts) >= 1
    root_post = posts[0]
    metadata = root_post.get("extra", {}).get("metadata", {})
    assert metadata.get("ls_agent_type") == "subagent", (
        f"ls_agent_type should be 'subagent' in tracer metadata, but got: {metadata}"
    )
    # Verify that the additional configurable key is merged into metadata
    assert metadata.get("custom_key") == "custom_value", (
        f"custom_key should be 'custom_value' in tracer metadata, but got: {metadata}"
    )