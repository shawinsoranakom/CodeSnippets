def test_responses_stream_function_call_preserves_namespace() -> None:
    """Test that namespace field is preserved in streaming function_call chunks."""
    function_call_stream = [
        ResponseCreatedEvent(
            response=Response(
                id="resp_ns",
                created_at=1749734255.0,
                error=None,
                incomplete_details=None,
                instructions=None,
                metadata={},
                model=MODEL,
                object="response",
                output=[],
                parallel_tool_calls=True,
                temperature=1.0,
                tool_choice="auto",
                tools=[],
                top_p=1.0,
                background=False,
                max_output_tokens=None,
                previous_response_id=None,
                reasoning=None,
                service_tier="auto",
                status="in_progress",
                text=ResponseTextConfig(format=ResponseFormatText(type="text")),
                truncation="disabled",
                usage=None,
                user=None,
            ),
            sequence_number=0,
            type="response.created",
        ),
        ResponseInProgressEvent(
            response=Response(
                id="resp_ns",
                created_at=1749734255.0,
                error=None,
                incomplete_details=None,
                instructions=None,
                metadata={},
                model=MODEL,
                object="response",
                output=[],
                parallel_tool_calls=True,
                temperature=1.0,
                tool_choice="auto",
                tools=[],
                top_p=1.0,
                background=False,
                max_output_tokens=None,
                previous_response_id=None,
                reasoning=None,
                service_tier="auto",
                status="in_progress",
                text=ResponseTextConfig(format=ResponseFormatText(type="text")),
                truncation="disabled",
                usage=None,
                user=None,
            ),
            sequence_number=1,
            type="response.in_progress",
        ),
        ResponseOutputItemAddedEvent(
            item=ResponseFunctionToolCallItem(
                id="fc_123",
                arguments="",
                call_id="call_123",
                name="search_tool",
                type="function_call",
                namespace="my_namespace",
                status="in_progress",
            ),
            output_index=0,
            sequence_number=2,
            type="response.output_item.added",
        ),
        ResponseFunctionCallArgumentsDeltaEvent(
            delta='{"query":',
            item_id="fc_123",
            output_index=0,
            sequence_number=3,
            type="response.function_call_arguments.delta",
        ),
        ResponseFunctionCallArgumentsDeltaEvent(
            delta='"test"}',
            item_id="fc_123",
            output_index=0,
            sequence_number=4,
            type="response.function_call_arguments.delta",
        ),
        ResponseFunctionCallArgumentsDoneEvent(
            arguments='{"query":"test"}',
            item_id="fc_123",
            name="search_tool",
            output_index=0,
            sequence_number=5,
            type="response.function_call_arguments.done",
        ),
        ResponseOutputItemDoneEvent(
            item=ResponseFunctionToolCallItem(
                id="fc_123",
                arguments='{"query":"test"}',
                call_id="call_123",
                name="search_tool",
                type="function_call",
                namespace="my_namespace",
                status="completed",
            ),
            output_index=0,
            sequence_number=6,
            type="response.output_item.done",
        ),
        ResponseCompletedEvent(
            response=Response(
                id="resp_ns",
                created_at=1749734255.0,
                error=None,
                incomplete_details=None,
                instructions=None,
                metadata={},
                model=MODEL,
                object="response",
                output=[
                    ResponseFunctionToolCallItem(
                        id="fc_123",
                        arguments='{"query":"test"}',
                        call_id="call_123",
                        name="search_tool",
                        type="function_call",
                        namespace="my_namespace",
                        status="completed",
                    ),
                ],
                parallel_tool_calls=True,
                temperature=1.0,
                tool_choice="auto",
                tools=[],
                top_p=1.0,
                background=False,
                max_output_tokens=None,
                previous_response_id=None,
                reasoning=None,
                service_tier="default",
                status="completed",
                text=ResponseTextConfig(format=ResponseFormatText(type="text")),
                truncation="disabled",
                usage=ResponseUsage(
                    input_tokens=10,
                    input_tokens_details=InputTokensDetails(cached_tokens=0),
                    output_tokens=20,
                    output_tokens_details=OutputTokensDetails(reasoning_tokens=0),
                    total_tokens=30,
                ),
                user=None,
            ),
            sequence_number=7,
            type="response.completed",
        ),
    ]

    llm = ChatOpenAI(model=MODEL, use_responses_api=True, output_version="responses/v1")
    mock_client = MagicMock()

    def mock_create(*args: Any, **kwargs: Any) -> MockSyncContextManager:
        return MockSyncContextManager(function_call_stream)

    mock_client.responses.create = mock_create

    full: BaseMessageChunk | None = None
    with patch.object(llm, "root_client", mock_client):
        for chunk in llm.stream("test"):
            assert isinstance(chunk, AIMessageChunk)
            full = chunk if full is None else full + chunk

    assert isinstance(full, AIMessageChunk)

    function_call_blocks = [
        block
        for block in full.content
        if isinstance(block, dict) and block.get("type") == "function_call"
    ]
    assert len(function_call_blocks) > 0

    first_block = function_call_blocks[0]
    assert first_block.get("namespace") == "my_namespace", (
        f"Expected namespace 'my_namespace', got {first_block.get('namespace')}"
    )