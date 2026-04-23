def test_tool_call(
    streaming: bool,
    model_output: str,
    expected_tool_calls: list[FunctionCall],
    expected_content: str | None,
    gigachat_tokenizer: TokenizerLike,
):
    tool_parser: ToolParser = ToolParserManager.get_tool_parser("gigachat3")(
        gigachat_tokenizer
    )
    content, tool_calls = run_tool_extraction(
        tool_parser, model_output, streaming=streaming
    )
    if content == "":
        content = None
    assert content == expected_content
    assert len(tool_calls) == len(expected_tool_calls)
    for actual, expected in zip(tool_calls, expected_tool_calls):
        assert actual.type == "function"
        assert actual.function.name == expected.name
        actual_args = json.loads(actual.function.arguments)
        expected_args = json.loads(expected.arguments)
        assert actual_args == expected_args