def test_extract_tool_calls_streaming_missing_opening_tag(
    qwen3_tool_parser_parametrized, qwen3_tokenizer
):
    """Test streaming with missing opening <tool_call> tag

    This tests that the streaming parser correctly handles
    tool calls that start directly with <function=...>
    """
    model_output = """I'll check the weather for you.

<function=get_current_weather>
<parameter=city>
Dallas
</parameter>
<parameter=state>
TX
</parameter>
<parameter=unit>
fahrenheit
</parameter>
</function>
</tool_call>"""

    request = ChatCompletionRequest(model=MODEL, messages=[])

    other_content = ""
    tool_states = {}

    for delta_message in stream_delta_message_generator(
        qwen3_tool_parser_parametrized, qwen3_tokenizer, model_output, request
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
    assert "I'll check the weather for you." in other_content

    # Verify we got the tool call
    assert len(tool_states) == 1
    assert len(qwen3_tool_parser_parametrized.prev_tool_call_arr) == 1

    state = tool_states[0]
    assert state["id"] is not None
    assert state["type"] == "function"
    assert state["name"] == "get_current_weather"

    # Verify arguments were parsed correctly despite missing opening tag
    assert state["arguments"] is not None
    args = json.loads(state["arguments"])
    assert args["city"] == "Dallas"
    assert args["state"] == "TX"
    assert args["unit"] == "fahrenheit"