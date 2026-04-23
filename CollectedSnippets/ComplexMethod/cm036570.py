def test_extract_tool_calls_missing_closing_parameter_tag(
    qwen3_tool_parser_parametrized,
):
    """Test handling of missing closing </parameter> tag"""
    # Using get_current_weather from sample_tools but with malformed XML
    model_output = """Let me check the weather for you:
<tool_call>
<function=get_current_weather>
<parameter=city>
Dallas
<parameter=state>
TX
</parameter>
<parameter=unit>
fahrenheit
</parameter>
</function>
</tool_call>"""

    request = ChatCompletionRequest(model=MODEL, messages=[])
    extracted_tool_calls = qwen3_tool_parser_parametrized.extract_tool_calls(
        model_output, request=request
    )

    # The parser should handle the malformed XML gracefully
    assert extracted_tool_calls.tools_called
    assert len(extracted_tool_calls.tool_calls) == 1

    # Verify the function name is correct
    assert extracted_tool_calls.tool_calls[0].function.name == "get_current_weather"

    # Verify the arguments are parsed despite the missing closing tag
    args = json.loads(extracted_tool_calls.tool_calls[0].function.arguments)
    assert "city" in args
    assert args["city"] == "Dallas"
    assert args["state"] == "TX"
    assert args["unit"] == "fahrenheit"

    # Check that content before the tool call is preserved
    assert "Let me check the weather for you:" in extracted_tool_calls.content