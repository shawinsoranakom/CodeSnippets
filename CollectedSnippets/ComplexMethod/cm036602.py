def test_extract_tool_calls_streaming_missing_closing_tag(
    step3p5_tool_parser, step3p5_tokenizer, sample_tools
):
    """Test streaming with missing closing </parameter> tag"""
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

    # Verify content was streamed
    assert "Let me check the weather for you:" in other_content

    # Verify we got the tool call
    assert len(tool_states) == 1
    state = tool_states[0]
    assert state["id"] is not None
    assert state["type"] == "function"
    assert state["name"] == "get_current_weather"

    # Verify arguments were parsed correctly despite missing closing tag
    assert state["arguments"] is not None
    args = json.loads(state["arguments"])
    assert args["city"] == "Dallas"
    assert args["state"] == "TX"
    assert args["unit"] == "fahrenheit"