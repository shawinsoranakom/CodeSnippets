def test_hermes_streaming_content_and_tool_call_in_single_chunk(
    qwen_tokenizer: TokenizerLike,
    any_chat_request: ChatCompletionRequest,
) -> None:
    """Content + complete tool call in one chunk must both be emitted."""
    text = 'Hi!<tool_call>{"name": "f", "arguments": {"x": 1}}</tool_call>'
    # Use a stream_interval large enough to guarantee a single chunk.
    parser = Hermes2ProToolParser(qwen_tokenizer)
    deltas = _simulate_streaming(
        qwen_tokenizer,
        parser,
        any_chat_request,
        text,
        stream_interval=9999,
    )

    content_parts = [d.content for d in deltas if d.content]
    tool_parts = [tc for d in deltas if d.tool_calls for tc in d.tool_calls]

    assert "".join(content_parts) == "Hi!"
    assert tool_parts[0].function.name == "f"
    args_str = "".join(tc.function.arguments or "" for tc in tool_parts)
    assert json.loads(args_str) == {"x": 1}