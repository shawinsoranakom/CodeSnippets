def test_extract_tool_calls_streaming_incremental(
    xlam_tool_parser,
    xlam_tokenizer,
    model_output,
    expected_tool_calls,
    expected_content,
):
    """Verify the XLAM Parser streaming behavior by verifying each chunk is as expected."""  # noqa: E501
    request = ChatCompletionRequest(model=MODEL, messages=[])

    chunks = []
    for delta_message in stream_delta_message_generator(
        xlam_tool_parser, xlam_tokenizer, model_output, request
    ):
        chunks.append(delta_message)

    # Should have multiple chunks
    assert len(chunks) >= 3

    # Should have a chunk with tool header (id, name, type) for the first tool call # noqa: E501
    header_found = False
    expected_first_tool = expected_tool_calls[0]
    for chunk in chunks:
        if chunk.tool_calls and chunk.tool_calls[0].id:
            header_found = True
            assert (
                chunk.tool_calls[0].function.name == expected_first_tool.function.name
            )
            assert chunk.tool_calls[0].type == "function"
            # Arguments may be empty initially or None
            if chunk.tool_calls[0].function.arguments is not None:
                # If present, should be empty string initially
                assert chunk.tool_calls[0].function.arguments == ""
            break
    assert header_found

    # Should have chunks with incremental arguments
    arg_chunks = []
    for chunk in chunks:
        if (
            chunk.tool_calls
            and chunk.tool_calls[0].function.arguments
            and chunk.tool_calls[0].function.arguments != ""
            and chunk.tool_calls[0].index
            == 0  # Only collect arguments from the first tool call
        ):
            arg_chunks.append(chunk.tool_calls[0].function.arguments)

    # Arguments should be streamed incrementally
    assert len(arg_chunks) > 1

    # Concatenated arguments should form valid JSON for the first tool call
    full_args = "".join(arg_chunks)
    parsed_args = json.loads(full_args)
    expected_args = json.loads(expected_first_tool.function.arguments)
    assert parsed_args == expected_args