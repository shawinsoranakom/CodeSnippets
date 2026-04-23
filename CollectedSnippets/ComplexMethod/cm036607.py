def test_extract_tool_calls_streaming_multiple_tool_calls_no_content_between(
    step3p5_tool_parser, step3p5_tokenizer, sample_tools
):
    """Test multiple tool calls with no content between them.

    Scenario: Model outputs "hello" + tool call + tool call
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

    other_content = ""
    tool_states = {}

    for delta_message in stream_delta_message_generator(
        step3p5_tool_parser, step3p5_tokenizer, model_output, request
    ):
        if delta_message.content:
            other_content += delta_message.content

        if delta_message.tool_calls:
            for tool_call in delta_message.tool_calls:
                idx = tool_call.index

                if idx not in tool_states:
                    tool_states[idx] = {
                        "id": None,
                        "name": None,
                        "arguments": "",
                        "type": None,
                    }

                if tool_call.id:
                    tool_states[idx]["id"] = tool_call.id

                if tool_call.type:
                    assert tool_call.type == "function"
                    tool_states[idx]["type"] = tool_call.type

                if tool_call.function:
                    if tool_call.function.name:
                        tool_states[idx]["name"] = tool_call.function.name

                    if tool_call.function.arguments is not None:
                        tool_states[idx]["arguments"] += tool_call.function.arguments

    # Should have exactly two complete tool calls
    assert len(tool_states) == 2, "Should have exactly two complete tool calls"

    # Verify the first tool call (index=0)
    assert tool_states[0]["name"] == "get_current_weather"
    assert tool_states[0]["arguments"]
    args_dict_0 = json.loads(tool_states[0]["arguments"])
    assert args_dict_0["city"] == "Dallas"
    assert args_dict_0["state"] == "TX"

    # Verify the second tool call (index=1)
    assert tool_states[1]["name"] == "calculate_area"
    assert tool_states[1]["arguments"]
    args_dict_1 = json.loads(tool_states[1]["arguments"])
    assert args_dict_1["shape"] == "rectangle"
    assert isinstance(args_dict_1["dimensions"], dict), "dimensions should be a dict"
    assert args_dict_1["dimensions"]["width"] == 10
    assert args_dict_1["dimensions"]["height"] == 5

    assert "hello" in other_content, "Should contain 'hello' as content"

    # Verify that tool call tags are NOT in the content
    assert "<function=get_current_weather>" not in other_content, (
        "First tool call should not be in content"
    )
    assert "<function=calculate_area>" not in other_content, (
        "Second tool call should not be in content"
    )