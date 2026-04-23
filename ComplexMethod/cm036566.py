def test_extract_tool_calls_numeric_deserialization(glm4_moe_tool_parser, mock_request):
    """Test that numeric arguments are deserialized as numbers, not strings."""
    model_output = """<tool_call>calculate
<arg_key>operation</arg_key>
<arg_value>add</arg_value>
<arg_key>a</arg_key>
<arg_value>42</arg_value>
<arg_key>b</arg_key>
<arg_value>3.14</arg_value>
<arg_key>enabled</arg_key>
<arg_value>true</arg_value>
</tool_call>"""

    extracted_tool_calls = glm4_moe_tool_parser.extract_tool_calls(
        model_output, request=mock_request
    )  # type: ignore[arg-type]

    assert extracted_tool_calls.tools_called
    assert len(extracted_tool_calls.tool_calls) == 1

    args = json.loads(extracted_tool_calls.tool_calls[0].function.arguments)

    # String should remain string
    assert args["operation"] == "add"
    assert isinstance(args["operation"], str)

    # Integer should be deserialized as int
    assert args["a"] == 42
    assert isinstance(args["a"], int)

    # Float should be deserialized as float
    assert args["b"] == 3.14
    assert isinstance(args["b"], float)

    # Boolean should be deserialized as bool
    assert args["enabled"] is True
    assert isinstance(args["enabled"], bool)