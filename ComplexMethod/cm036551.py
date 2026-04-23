def test_hermes_streaming_boolean_args_with_stream_interval(
    qwen_tokenizer: TokenizerLike,
    any_chat_request: ChatCompletionRequest,
    stream_interval: int,
) -> None:
    """Regression test for bug #19056 with stream_interval > 1."""
    text = (
        "<tool_call>\n"
        '{"name": "final_answer", "arguments": {"trigger": true}}\n'
        "</tool_call>"
    )
    parser = Hermes2ProToolParser(qwen_tokenizer)
    deltas = _simulate_streaming(
        qwen_tokenizer, parser, any_chat_request, text, stream_interval
    )

    tool_calls = [tc for d in deltas if d.tool_calls for tc in d.tool_calls]
    assert tool_calls[0].function.name == "final_answer"
    args_str = "".join(tc.function.arguments or "" for tc in tool_calls)
    assert json.loads(args_str) == {"trigger": True}