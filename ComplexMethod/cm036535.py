def test_mistral_function_call_nested_json():
    """Ensure that the function-name regex captures the entire outermost
    JSON block, including nested braces."""

    # Create a minimal stub tokenizer that provides the few attributes the
    # parser accesses (`version` and `get_vocab`).
    class _StubMistralTokenizer(MistralTokenizer):
        version = 11  # Satisfy the version check

        def __init__(self):
            pass

        @staticmethod
        def get_vocab():
            # Provide the special TOOL_CALLS token expected by the parser.
            return {"[TOOL_CALLS]": 0}

    tokenizer = _StubMistralTokenizer()
    parser = MistralToolParser(tokenizer)

    # Craft a model output featuring nested JSON inside the arguments.
    args_dict = {
        "city": "Dallas",
        "state": "TX",
        "unit": "fahrenheit",
        "sub_dict": {"foo": "bar", "inner": {"x": 1, "y": 2}},
    }

    model_output = f"{parser.bot_token}get_current_weather{json.dumps(args_dict)}"

    parsed = parser.extract_tool_calls(model_output, None)

    # Assertions: the tool call is detected and the full nested JSON is parsed
    # without truncation.
    assert parsed.tools_called

    assert MistralToolCall.is_valid_id(parsed.tool_calls[0].id)
    assert parsed.tool_calls[0].function.name == "get_current_weather"
    assert json.loads(parsed.tool_calls[0].function.arguments) == args_dict
    # No additional content outside the tool call should be returned.
    assert parsed.content is None

    # multiple calls
    multiple_args_dict = [
        {
            "city": "Dallas",
            "state": "TX",
            "unit": "fahrenheit",
            "sub_dict": {"foo": "bar", "inner": {"x": 1, "y": 2}},
        },
        {},
        {"a": 0},
        {"a": 1, "b": "c"},
    ]
    names = ["get_current_weather", "get_current_weather_2", "random", "random_2"]

    model_output = "".join(
        [
            f"{parser.bot_token}{name}{json.dumps(args)}"
            for name, args in zip(names, multiple_args_dict)
        ]
    )

    parsed = parser.extract_tool_calls(model_output, None)

    # Assertions: the tool call is detected and the full nested JSON is parsed
    # without truncation.
    assert parsed.tools_called
    assert len(parsed.tool_calls) == len(multiple_args_dict)

    for i, tool_call in enumerate(parsed.tool_calls):
        assert MistralToolCall.is_valid_id(tool_call.id)
        assert tool_call.function.name == names[i]
        assert json.loads(tool_call.function.arguments) == multiple_args_dict[i]
        # No additional content outside the tool call should be returned.
        assert parsed.content is None