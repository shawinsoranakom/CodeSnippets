def test_extract_tool_calls_streaming_incremental(
    ernie45_tool_parser,
    ernie45_tokenizer,
    model_output,
    expected_tool_calls,
    expected_content,
):
    """Verify the Ernie45 Parser streaming behavior by verifying each chunk is as expected."""  # noqa: E501
    request = ChatCompletionRequest(model=MODEL, messages=[])

    tool_calls_dict = {}
    for delta_message in stream_delta_message_generator(
        ernie45_tool_parser, ernie45_tokenizer, model_output, request
    ):
        if (
            delta_message.role is None
            and delta_message.content is None
            and delta_message.reasoning is None
            and len(delta_message.tool_calls) == 0
        ):
            continue
        tool_calls = delta_message.tool_calls
        for tool_call_chunk in tool_calls:
            index = tool_call_chunk.index
            if index not in tool_calls_dict:
                if tool_call_chunk.function.arguments is None:
                    tool_call_chunk.function.arguments = ""
                tool_calls_dict[index] = tool_call_chunk
            else:
                tool_calls_dict[
                    index
                ].function.arguments += tool_call_chunk.function.arguments
    actual_tool_calls = list(tool_calls_dict.values())

    assert len(actual_tool_calls) > 0
    # check tool call format
    assert_tool_calls(actual_tool_calls, expected_tool_calls)