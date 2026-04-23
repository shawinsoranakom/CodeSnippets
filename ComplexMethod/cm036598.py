def test_build_non_streaming_tool_calls(
    tool_calls: list[VllmFunctionCall] | None,
    expected_len: int,
) -> None:
    result = MistralToolParser.build_non_streaming_tool_calls(tool_calls)
    assert len(result) == expected_len

    if tool_calls is None:
        return

    for i, tc in enumerate(result):
        assert isinstance(tc, MistralToolCall)
        assert tc.type == "function"

        input_tc = tool_calls[i]
        if input_tc.id:
            assert tc.id == input_tc.id
        else:
            assert len(tc.id) == 9
            assert tc.id.isalnum()

        assert tc.function.name == input_tc.name
        assert tc.function.arguments == input_tc.arguments