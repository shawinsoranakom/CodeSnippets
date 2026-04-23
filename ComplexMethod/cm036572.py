def test_extract_tool_calls_streaming_incremental(
    qwen3_tool_parser_parametrized, qwen3_tokenizer
):
    """Test that streaming is truly incremental"""
    model_output = """I'll check the weather.<tool_call>
<function=get_current_weather>
<parameter=city>
Dallas
</parameter>
<parameter=state>
TX
</parameter>
</function>
</tool_call>"""

    request = ChatCompletionRequest(model=MODEL, messages=[])

    chunks = []
    for delta_message in stream_delta_message_generator(
        qwen3_tool_parser_parametrized, qwen3_tokenizer, model_output, request
    ):
        chunks.append(delta_message)

    # Should have multiple chunks
    assert len(chunks) > 3

    # First chunk(s) should be content
    assert chunks[0].content is not None
    assert chunks[0].tool_calls is None or chunks[0].tool_calls == []

    # Should have a chunk with tool header (id, name, type)
    header_found = False
    for chunk in chunks:
        if chunk.tool_calls and chunk.tool_calls[0].id:
            header_found = True
            assert chunk.tool_calls[0].function.name == "get_current_weather"
            assert chunk.tool_calls[0].type == "function"
            # Empty initially
            assert chunk.tool_calls[0].function.arguments == ""
            break
    assert header_found

    # Should have chunks with incremental arguments
    arg_chunks = []
    for chunk in chunks:
        if chunk.tool_calls and chunk.tool_calls[0].function.arguments:
            arg_chunks.append(chunk.tool_calls[0].function.arguments)

    # Arguments should be streamed incrementally
    assert len(arg_chunks) > 1

    # Concatenated arguments should form valid JSON
    full_args = "".join(arg_chunks)
    parsed_args = json.loads(full_args)
    assert parsed_args["city"] == "Dallas"
    assert parsed_args["state"] == "TX"