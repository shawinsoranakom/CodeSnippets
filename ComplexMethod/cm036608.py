def test_extract_tool_calls_streaming_multi_token_chunk_boundary(
    step3p5_tool_parser, step3p5_tokenizer, sample_tools
):
    """Ensure fallback doesn't close a new tool_call when boundary is in one chunk."""
    request = ChatCompletionRequest(model=MODEL, messages=[], tools=sample_tools)
    delta_text_chunks = [
        """<tool_call>
<function=get_current_weather>
<parameter=city>
Sys""",
        """
</parameter>
</function>
""",
        """</tool_call><tool_call>
<""",
        """function=calculate_area>
<parameter=shape>
rectangle""",
        """</parameter>
</function>
</tool_call>""",
    ]
    boundary_chunk = delta_text_chunks[1]
    assert len(step3p5_tokenizer.encode(boundary_chunk, add_special_tokens=False)) > 1

    tool_states = {}
    for delta_message in stream_delta_message_generator_from_chunks(
        step3p5_tool_parser, step3p5_tokenizer, delta_text_chunks, request
    ):
        print(delta_message)
        if delta_message.tool_calls:
            for tool_call in delta_message.tool_calls:
                idx = tool_call.index
                if idx not in tool_states:
                    tool_states[idx] = {
                        "name": None,
                        "arguments": "",
                    }
                if tool_call.function:
                    if tool_call.function.name:
                        tool_states[idx]["name"] = tool_call.function.name
                    if tool_call.function.arguments is not None:
                        tool_states[idx]["arguments"] += tool_call.function.arguments

    assert len(tool_states) == 2
    assert all(state["name"] for state in tool_states.values())
    assert tool_states[0]["name"] == "get_current_weather"
    assert tool_states[1]["name"] == "calculate_area"