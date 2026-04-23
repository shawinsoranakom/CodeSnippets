def test__construct_lc_result_from_responses_api_function_call_valid_json() -> None:
    """Test a response with a valid function call."""
    response = Response(
        id="resp_123",
        created_at=1234567890,
        model="gpt-4o",
        object="response",
        parallel_tool_calls=True,
        tools=[],
        tool_choice="auto",
        output=[
            ResponseFunctionToolCall(
                type="function_call",
                id="func_123",
                call_id="call_123",
                name="get_weather",
                arguments='{"location": "New York", "unit": "celsius"}',
            )
        ],
    )

    # v0
    result = _construct_lc_result_from_responses_api(response, output_version="v0")

    msg: AIMessage = cast(AIMessage, result.generations[0].message)
    assert len(msg.tool_calls) == 1
    assert msg.tool_calls[0]["type"] == "tool_call"
    assert msg.tool_calls[0]["name"] == "get_weather"
    assert msg.tool_calls[0]["id"] == "call_123"
    assert msg.tool_calls[0]["args"] == {"location": "New York", "unit": "celsius"}
    assert _FUNCTION_CALL_IDS_MAP_KEY in result.generations[0].message.additional_kwargs
    assert (
        result.generations[0].message.additional_kwargs[_FUNCTION_CALL_IDS_MAP_KEY][
            "call_123"
        ]
        == "func_123"
    )

    # responses/v1
    result = _construct_lc_result_from_responses_api(response)
    msg = cast(AIMessage, result.generations[0].message)
    assert msg.tool_calls
    assert msg.content == [
        {
            "type": "function_call",
            "id": "func_123",
            "name": "get_weather",
            "arguments": '{"location": "New York", "unit": "celsius"}',
            "call_id": "call_123",
        }
    ]