def assert_tool_calls(
    actual_tool_calls: list[ToolCall], expected_tool_calls: list[ToolCall]
):
    assert len(actual_tool_calls) == len(expected_tool_calls)

    for actual_tool_call, expected_tool_call in zip(
        actual_tool_calls, expected_tool_calls
    ):
        assert isinstance(actual_tool_call.id, str)
        assert len(actual_tool_call.id) > 0

        assert actual_tool_call.type == "function"
        assert actual_tool_call.function.name == expected_tool_call.function.name
        # Compare arguments as JSON objects to handle formatting differences
        actual_args = json.loads(actual_tool_call.function.arguments)
        expected_args = json.loads(expected_tool_call.function.arguments)
        assert actual_args == expected_args