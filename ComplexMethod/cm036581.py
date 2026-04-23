def test_preprocess_model_output(xlam_tool_parser):
    # Test with list structure
    model_output = (
        """[{"name": "get_current_weather", "arguments": {"city": "Seattle"}}]"""  # noqa: E501
    )
    content, potential_tool_calls = xlam_tool_parser.preprocess_model_output(
        model_output
    )
    assert content is None
    assert potential_tool_calls == model_output

    # Test with thinking tag
    model_output = """<think>I'll help you with that.</think>[{"name": "get_current_weather", "arguments": {"city": "Seattle"}}]"""  # noqa: E501
    content, potential_tool_calls = xlam_tool_parser.preprocess_model_output(
        model_output
    )
    assert content == "<think>I'll help you with that.</think>"
    assert (
        potential_tool_calls
        == '[{"name": "get_current_weather", "arguments": {"city": "Seattle"}}]'
    )

    # Test with JSON code block
    model_output = """I'll help you with that.
```json
[{"name": "get_current_weather", "arguments": {"city": "Seattle"}}]
```"""
    content, potential_tool_calls = xlam_tool_parser.preprocess_model_output(
        model_output
    )
    assert content == "I'll help you with that."
    assert "get_current_weather" in potential_tool_calls

    # Test with no tool calls
    model_output = """I'll help you with that."""
    content, potential_tool_calls = xlam_tool_parser.preprocess_model_output(
        model_output
    )
    assert content == model_output
    assert potential_tool_calls is None