def stream_delta_message_generator(
    mistral_tool_parser: MistralToolParser,
    mistral_tokenizer: TokenizerLike,
    model_output: str | None,
    tools: list[tuple[str, str]] | None,
) -> Generator[DeltaMessage, None, None]:
    if (
        isinstance(mistral_tokenizer, MistralTokenizer)
        and mistral_tokenizer.version >= 11
    ):
        # With the newer versions of the tokenizer,
        # we cannot tokenize free text
        # so we need to create a list of messages to get tokenized
        assert tools is not None
        assistant_msg = AssistantMessage(
            tool_calls=[
                ToolCall(
                    function=FunctionCall(
                        name=name,
                        arguments=arg,
                    )
                )
                for (name, arg) in tools
            ],
        )
        request = InstructRequest(
            messages=[assistant_msg],
        )
        all_token_ids = mistral_tokenizer.instruct.encode_instruct(request).tokens
    else:
        # Older versions of the tokenizer are
        # able to encode directly the model's output (free text) into tokens
        assert model_output is not None
        all_token_ids = mistral_tokenizer.encode(model_output, add_special_tokens=False)

    all_token_ids = fix_tool_call_tokenization(
        all_token_ids, mistral_tool_parser, mistral_tokenizer
    )

    previous_text = ""
    previous_tokens = None
    prefix_offset = 0
    read_offset = 0
    for i, delta_token in enumerate(all_token_ids):
        delta_token_ids = [delta_token]
        previous_token_ids = all_token_ids[:i]
        current_token_ids = all_token_ids[: i + 1]

        (new_tokens, delta_text, new_prefix_offset, new_read_offset) = (
            detokenize_incrementally(
                tokenizer=mistral_tokenizer,
                all_input_ids=current_token_ids,
                prev_tokens=previous_tokens,
                prefix_offset=prefix_offset,
                read_offset=read_offset,
                skip_special_tokens=isinstance(mistral_tokenizer, MistralTokenizer),
                spaces_between_special_tokens=True,
            )
        )

        current_text = previous_text + delta_text

        delta_message = mistral_tool_parser.extract_tool_calls_streaming(
            previous_text,
            current_text,
            delta_text,
            previous_token_ids,
            current_token_ids,
            delta_token_ids,
            request=_DUMMY_REQUEST,
        )
        if delta_message:
            yield delta_message

        previous_text = current_text
        previous_tokens = (
            previous_tokens + new_tokens if previous_tokens else new_tokens
        )
        prefix_offset = new_prefix_offset
        read_offset = new_read_offset