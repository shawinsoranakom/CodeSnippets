def test_mcp_tracing() -> None:
    # Test we exclude sensitive information from traces
    llm = ChatOpenAI(
        model="o4-mini", use_responses_api=True, output_version="responses/v1"
    )

    tracer = FakeTracer()
    mock_client = MagicMock()

    def mock_create(*args: Any, **kwargs: Any) -> MagicMock:
        mock_raw_response = MagicMock()
        mock_raw_response.parse.return_value = Response(
            id="resp_123",
            created_at=1234567890,
            model="o4-mini",
            object="response",
            parallel_tool_calls=True,
            tools=[],
            tool_choice="auto",
            output=[
                ResponseOutputMessage(
                    type="message",
                    id="msg_123",
                    content=[
                        ResponseOutputText(
                            type="output_text", text="Test response", annotations=[]
                        )
                    ],
                    role="assistant",
                    status="completed",
                )
            ],
        )
        return mock_raw_response

    mock_client.responses.with_raw_response.create = mock_create
    input_message = HumanMessage("Test query")
    tools = [
        {
            "type": "mcp",
            "server_label": "deepwiki",
            "server_url": "https://mcp.deepwiki.com/mcp",
            "require_approval": "always",
            "headers": {"Authorization": "Bearer PLACEHOLDER"},
        }
    ]
    with patch.object(llm, "root_client", mock_client):
        llm_with_tools = llm.bind_tools(tools)
        _ = llm_with_tools.invoke([input_message], config={"callbacks": [tracer]})

    # Test headers are not traced
    assert len(tracer.chat_model_start_inputs) == 1
    invocation_params = tracer.chat_model_start_inputs[0]["kwargs"]["invocation_params"]
    for tool in invocation_params["tools"]:
        if "headers" in tool:
            assert tool["headers"] == "**REDACTED**"
    for substring in ["Authorization", "Bearer", "PLACEHOLDER"]:
        assert substring not in str(tracer.chat_model_start_inputs)

    # Test headers are correctly propagated to request
    payload = llm_with_tools._get_request_payload([input_message], tools=tools)  # type: ignore[attr-defined]
    assert payload["tools"][0]["headers"]["Authorization"] == "Bearer PLACEHOLDER"