def test_extract_tool_calls_streaming(
    step3p5_tool_parser,
    step3p5_tokenizer,
    sample_tools,
    model_output,
    expected_tool_calls,
    expected_content,
):
    """Test incremental streaming behavior including typed parameters"""
    request = ChatCompletionRequest(model=MODEL, messages=[], tools=sample_tools)

    other_content = ""
    tool_states = {}  # Track state per tool index

    for delta_message in stream_delta_message_generator(
        step3p5_tool_parser, step3p5_tokenizer, model_output, request
    ):
        # role should never be streamed from tool parser
        assert not delta_message.role

        if delta_message.content:
            other_content += delta_message.content

        if delta_message.tool_calls:
            for tool_call in delta_message.tool_calls:
                idx = tool_call.index

                # Initialize state for new tool
                if idx not in tool_states:
                    tool_states[idx] = {
                        "id": None,
                        "name": None,
                        "arguments": "",
                        "type": None,
                    }

                # First chunk should have id, name, and type
                if tool_call.id:
                    tool_states[idx]["id"] = tool_call.id

                if tool_call.type:
                    assert tool_call.type == "function"
                    tool_states[idx]["type"] = tool_call.type

                if tool_call.function:
                    if tool_call.function.name:
                        # Should only be set once
                        assert tool_states[idx]["name"] is None
                        tool_states[idx]["name"] = tool_call.function.name

                    if tool_call.function.arguments is not None:
                        # Accumulate arguments incrementally
                        tool_states[idx]["arguments"] += tool_call.function.arguments

    # Verify final content
    assert other_content == (expected_content or "")  # Handle None case

    # Verify we got all expected tool calls
    assert len(tool_states) == len(expected_tool_calls)

    # Verify each tool call
    for idx, expected_tool in enumerate(expected_tool_calls):
        state = tool_states[idx]
        assert state["id"] is not None
        assert state["type"] == "function"
        assert state["name"] == expected_tool.function.name

        # Parse accumulated arguments
        arguments_str = state["arguments"]
        assert arguments_str is not None
        actual_args = json.loads(arguments_str)
        expected_args = json.loads(expected_tool.function.arguments)
        assert actual_args == expected_args