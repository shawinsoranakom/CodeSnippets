def test__construct_lc_result_from_responses_api_function_call_invalid_json() -> None:
    """Test a response with an invalid JSON function call."""
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
                arguments='{"location": "New York", "unit": "celsius"',
                # Missing closing brace
            )
        ],
    )

    result = _construct_lc_result_from_responses_api(response, output_version="v0")

    msg: AIMessage = cast(AIMessage, result.generations[0].message)
    assert len(msg.invalid_tool_calls) == 1
    assert msg.invalid_tool_calls[0]["type"] == "invalid_tool_call"
    assert msg.invalid_tool_calls[0]["name"] == "get_weather"
    assert msg.invalid_tool_calls[0]["id"] == "call_123"
    assert (
        msg.invalid_tool_calls[0]["args"]
        == '{"location": "New York", "unit": "celsius"'
    )
    assert "error" in msg.invalid_tool_calls[0]
    assert _FUNCTION_CALL_IDS_MAP_KEY in result.generations[0].message.additional_kwargs