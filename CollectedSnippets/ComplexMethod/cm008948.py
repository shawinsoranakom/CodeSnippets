def test_ls_agent_type_is_trace_only_metadata() -> None:
    """Test that ls_agent_type is added to metadata on tracing only, not in streamed chunks."""
    # Capture metadata from regular callback handler (simulates streamed metadata)
    captured_callback_metadata: list[dict[str, Any]] = []

    class CaptureHandler(BaseCallbackHandler):
        def on_chain_start(
            self,
            serialized: dict[str, Any],
            inputs: dict[str, Any],
            *,
            run_id: str,
            parent_run_id: str | None = None,
            tags: list[str] | None = None,
            metadata: dict[str, Any] | None = None,
            **kwargs: Any,
        ) -> None:
            captured_callback_metadata.append({"tags": tags, "metadata": metadata})

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
            config={"callbacks": [CaptureHandler()]},
        )

    # Verify that ls_agent_type is NOT in the regular callback metadata
    # (it should only go to the tracer via langsmith_inheritable_metadata)
    assert len(captured_callback_metadata) > 0
    for captured in captured_callback_metadata:
        metadata = captured.get("metadata") or {}
        assert metadata.get("ls_agent_type") is None, (
            f"ls_agent_type should not be in callback metadata, but got: {metadata}"
        )

    # Verify that ls_agent_type IS in the tracer metadata (sent to LangSmith)
    # Get the POST requests to the LangSmith API
    posts = []
    for call in mock_session.request.mock_calls:
        if call.args and call.args[0] == "POST":
            body = json.loads(call.kwargs["data"])
            if "post" in body:
                posts.extend(body["post"])
            else:
                posts.append(body)

    assert len(posts) >= 1
    # Find the root run (the agent execution)
    root_post = posts[0]
    metadata = root_post.get("extra", {}).get("metadata", {})
    assert metadata.get("ls_agent_type") == "root", (
        f"ls_agent_type should be 'root' in tracer metadata, but got: {metadata}"
    )