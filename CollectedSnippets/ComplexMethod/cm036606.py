def test_extract_tool_calls_streaming_full_input_mixed_content_and_multiple_tool_calls(
    step3p5_tool_parser, step3p5_tokenizer, sample_tools
):
    """Test streaming with entire input as single delta_text.

    Scenario: Model outputs "hello" + complete tool call + "hi" + complete tool call.
    This test simulates the case where the entire input is sent as a single delta_text.
    Expected: "hello" as content, first tool call parsed (index=0), "hi" as content,
    second tool call parsed (index=1).
    """
    # Model output: hello + complete tool call + hi + complete tool call
    model_output = """hello<tool_call>
<function=get_current_weather>
<parameter=city>
Dallas
</parameter>
<parameter=state>
TX
</parameter>
</function>
</tool_call>hi<tool_call>
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

    # Encode all content tokens at once
    all_token_ids = step3p5_tokenizer.encode(model_output, add_special_tokens=False)
    eos_token_id = step3p5_tokenizer.eos_token_id

    # Include EOS token in delta_token_ids if available
    if eos_token_id is not None:
        delta_token_ids = all_token_ids + [eos_token_id]
    else:
        delta_token_ids = all_token_ids

    # current_token_ids includes all content tokens (EOS is not part of the text)
    current_token_ids = all_token_ids
    previous_token_ids: list[int] = []

    # Decode all tokens to get the full text
    current_text = step3p5_tokenizer.decode(
        current_token_ids, skip_special_tokens=False
    )
    previous_text = ""
    delta_text = current_text

    # Call parser once with all tokens including EOS
    delta_result = step3p5_tool_parser.extract_tool_calls_streaming(
        previous_text,
        current_text,
        delta_text,
        previous_token_ids,
        current_token_ids,
        delta_token_ids,
        request=request,
    )

    # Process delta result
    if delta_result:
        if delta_result.content:
            other_content += delta_result.content
        if delta_result.tool_calls:
            for tool_call in delta_result.tool_calls:
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

    # Verify content: should contain "hello", "hi"
    assert "hello" in other_content, "Should contain 'hello' as content"
    assert "hi" in other_content, "Should contain 'hi' as content"

    # Verify the order: hello should come first, then hi
    hello_index = other_content.find("hello")
    hi_index = other_content.find("hi")

    assert hello_index >= 0, "'hello' should be in content"
    assert hi_index > hello_index, "'hi' should come after 'hello'"

    # Verify that tool call tags are NOT in the content
    assert "<function=get_current_weather>" not in other_content, (
        "First tool call should not be in content"
    )
    assert "<function=calculate_area>" not in other_content, (
        "Second tool call should not be in content"
    )