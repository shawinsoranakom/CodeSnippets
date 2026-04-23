def test_extract_tool_calls_streaming_v11_no_tools(
    mistral_tool_parser, mistral_tokenizer
):
    model_output = "This is a test"
    if isinstance(mistral_tokenizer, MistralTokenizer):
        all_token_ids = mistral_tokenizer.encode(model_output)
    else:
        all_token_ids = mistral_tokenizer.encode(model_output, add_special_tokens=False)
    skip_special = isinstance(mistral_tokenizer, MistralTokenizer)
    collected_content = ""
    previous_text = ""
    previous_tokens = None
    prefix_offset = 0
    read_offset = 0
    for i in range(len(all_token_ids)):
        current_token_ids = all_token_ids[: i + 1]
        previous_token_ids = all_token_ids[:i]
        delta_token_ids = [all_token_ids[i]]

        new_tokens, delta_text, prefix_offset, read_offset = detokenize_incrementally(
            tokenizer=mistral_tokenizer,
            all_input_ids=current_token_ids,
            prev_tokens=previous_tokens,
            prefix_offset=prefix_offset,
            read_offset=read_offset,
            skip_special_tokens=skip_special,
            spaces_between_special_tokens=True,
        )
        current_text = previous_text + delta_text
        previous_tokens = (
            previous_tokens + new_tokens if previous_tokens else new_tokens
        )

        delta_message = mistral_tool_parser.extract_tool_calls_streaming(
            previous_text=previous_text,
            current_text=current_text,
            delta_text=delta_text,
            previous_token_ids=previous_token_ids,
            current_token_ids=current_token_ids,
            delta_token_ids=delta_token_ids,
            request=_DUMMY_REQUEST,
        )
        if delta_message and delta_message.content:
            collected_content += delta_message.content
        if delta_message:
            assert not delta_message.tool_calls

        previous_text = current_text

    assert collected_content == model_output