def test_extract_tool_calls_non_streaming_multiple_tool_calls_no_content_between(
    step3p5_tool_parser, sample_tools
):
    """Test non-streaming extraction with tool calls and no content between them.

    Scenario: Model outputs "hello" + tool call + tool call.
    Expected: "hello" as content, first tool call parsed (index=0),
    second tool call parsed (index=1).
    No content should appear between the two tool calls.
    """
    # Model output: hello + tool call + tool call (no content between tool calls)
    model_output = """hello<tool_call>
<function=get_current_weather>
<parameter=city>
Dallas
</parameter>
<parameter=state>
TX
</parameter>
</function>
</tool_call><tool_call>
<function=calculate_area>
<parameter=shape>
rectangle
</parameter>
<parameter=dimensions>
{"width": 10, "height": 5}
</parameter>
</function>
</tool_call>"""

    request = ChatCompletionRequest(model=MODEL, messages=[], tools=sample_tools)

    extracted_tool_calls = step3p5_tool_parser.extract_tool_calls(
        model_output, request=request
    )

    # Should have exactly two complete tool calls
    assert extracted_tool_calls.tools_called
    assert len(extracted_tool_calls.tool_calls) == 2, (
        "Should have exactly two complete tool calls"
    )

    # Verify the first tool call (index=0)
    assert extracted_tool_calls.tool_calls[0].function.name == "get_current_weather"
    args_dict_0 = json.loads(extracted_tool_calls.tool_calls[0].function.arguments)
    assert args_dict_0["city"] == "Dallas"
    assert args_dict_0["state"] == "TX"

    # Verify the second tool call (index=1)
    assert extracted_tool_calls.tool_calls[1].function.name == "calculate_area"
    args_dict_1 = json.loads(extracted_tool_calls.tool_calls[1].function.arguments)
    assert args_dict_1["shape"] == "rectangle"
    assert isinstance(args_dict_1["dimensions"], dict), "dimensions should be a dict"
    assert args_dict_1["dimensions"]["width"] == 10
    assert args_dict_1["dimensions"]["height"] == 5

    # Verify content: should contain "hello"
    assert extracted_tool_calls.content is not None
    assert "hello" in extracted_tool_calls.content, "Should contain 'hello' as content"

    # Verify that tool call tags are NOT in the content
    assert "<function=get_current_weather>" not in extracted_tool_calls.content, (
        "First tool call should not be in content"
    )
    assert "<function=calculate_area>" not in extracted_tool_calls.content, (
        "Second tool call should not be in content"
    )