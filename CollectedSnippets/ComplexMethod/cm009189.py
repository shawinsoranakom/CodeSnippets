def test__construct_lc_result_from_responses_api_complex_response() -> None:
    """Test a complex response with multiple output types."""
    response = Response(
        id="resp_123",
        created_at=1234567890,
        model="gpt-4o",
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
                        type="output_text",
                        text="Here's the information you requested:",
                        annotations=[],
                    )
                ],
                role="assistant",
                status="completed",
            ),
            ResponseFunctionToolCall(
                type="function_call",
                id="func_123",
                call_id="call_123",
                name="get_weather",
                arguments='{"location": "New York"}',
            ),
        ],
        metadata={"key1": "value1", "key2": "value2"},
        incomplete_details=IncompleteDetails(reason="max_output_tokens"),
        status="completed",
        user="user_123",
    )

    # v0
    result = _construct_lc_result_from_responses_api(response, output_version="v0")

    # Check message content
    assert result.generations[0].message.content == [
        {
            "type": "text",
            "text": "Here's the information you requested:",
            "annotations": [],
        }
    ]

    # Check tool calls
    msg: AIMessage = cast(AIMessage, result.generations[0].message)
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0]["name"] == "get_weather"

    # Check metadata
    assert result.generations[0].message.response_metadata["id"] == "resp_123"
    assert result.generations[0].message.response_metadata["metadata"] == {
        "key1": "value1",
        "key2": "value2",
    }
    assert result.generations[0].message.response_metadata["incomplete_details"] == {
        "reason": "max_output_tokens"
    }
    assert result.generations[0].message.response_metadata["status"] == "completed"
    assert result.generations[0].message.response_metadata["user"] == "user_123"

    # responses/v1
    result = _construct_lc_result_from_responses_api(response)
    msg = cast(AIMessage, result.generations[0].message)
    assert msg.response_metadata["metadata"] == {"key1": "value1", "key2": "value2"}
    assert msg.content == [
        {
            "type": "text",
            "text": "Here's the information you requested:",
            "annotations": [],
            "id": "msg_123",
        },
        {
            "type": "function_call",
            "id": "func_123",
            "call_id": "call_123",
            "name": "get_weather",
            "arguments": '{"location": "New York"}',
        },
    ]