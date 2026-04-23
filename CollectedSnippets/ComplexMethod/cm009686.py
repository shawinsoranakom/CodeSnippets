def test_json_output_key_tools_parser_parameter_combinations(
    *, use_tool_calls: bool
) -> None:
    """Test all parameter combinations of JsonOutputKeyToolsParser."""

    def create_message() -> AIMessage:
        tool_calls_data = [
            {
                "id": "call_other",
                "function": {"name": "other", "arguments": '{"b":2}'},
                "type": "function",
            },
            {
                "id": "call_func1",
                "function": {"name": "func", "arguments": '{"a":1}'},
                "type": "function",
            },
            {
                "id": "call_func2",
                "function": {"name": "func", "arguments": '{"a":3}'},
                "type": "function",
            },
        ]

        if use_tool_calls:
            return AIMessage(
                content="",
                tool_calls=[
                    {"id": "call_other", "name": "other", "args": {"b": 2}},
                    {"id": "call_func1", "name": "func", "args": {"a": 1}},
                    {"id": "call_func2", "name": "func", "args": {"a": 3}},
                ],
            )
        return AIMessage(
            content="",
            additional_kwargs={"tool_calls": tool_calls_data},
        )

    result: list[ChatGeneration] = [ChatGeneration(message=create_message())]

    # Test: first_tool_only=True, return_id=True
    parser1 = JsonOutputKeyToolsParser(
        key_name="func", first_tool_only=True, return_id=True
    )
    output1 = parser1.parse_result(result)  # type: ignore[arg-type]
    assert output1["type"] == "func"
    assert output1["args"] == {"a": 1}
    assert "id" in output1

    # Test: first_tool_only=True, return_id=False
    parser2 = JsonOutputKeyToolsParser(
        key_name="func", first_tool_only=True, return_id=False
    )
    output2 = parser2.parse_result(result)  # type: ignore[arg-type]
    assert output2 == {"a": 1}

    # Test: first_tool_only=False, return_id=True
    parser3 = JsonOutputKeyToolsParser(
        key_name="func", first_tool_only=False, return_id=True
    )
    output3 = parser3.parse_result(result)  # type: ignore[arg-type]
    assert len(output3) == 2
    assert all("id" in item for item in output3)
    assert output3[0]["args"] == {"a": 1}
    assert output3[1]["args"] == {"a": 3}

    # Test: first_tool_only=False, return_id=False
    parser4 = JsonOutputKeyToolsParser(
        key_name="func", first_tool_only=False, return_id=False
    )
    output4 = parser4.parse_result(result)  # type: ignore[arg-type]
    assert output4 == [{"a": 1}, {"a": 3}]