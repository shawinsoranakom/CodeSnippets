async def send_turn(
    session: aiohttp.ClientSession,
    client_id: int,
    conv_id: str,
    conversation_messages: MessagesList,
    messages_to_use: int,
    tokenizer: AutoTokenizer,
    req_args: RequestArgs,
    verbose: bool,
    verify_output: bool,
) -> RequestStats | None:
    assert messages_to_use > 0
    assert messages_to_use <= len(conversation_messages)

    messages = conversation_messages[:messages_to_use]

    # Index of the next message (the role should be "user")
    index = messages_to_use - 1

    # Verify that the message has only two keys, "role" and "content"
    assert len(messages[index].keys()) == 2
    assert "role" in messages[index] and "content" in messages[index]
    assert messages[index]["role"] == "user", (
        f"Failed on conversation ID {conv_id}, message role should be user"
    )

    if verbose:
        print(
            f"{Color.CYAN}Messages (conversation ID {conv_id},"
            f" {len(messages)} turns):{Color.RESET}",
            messages,
        )

    # None means that there is no upper/lower limit for the output token count
    min_tokens = None if req_args.limit_min_tokens < 0 else req_args.limit_min_tokens
    max_tokens = None if req_args.limit_max_tokens < 0 else req_args.limit_max_tokens

    if len(conversation_messages) > messages_to_use:
        # The conversation contains an assistant answer for the next user prompt
        if (
            min_tokens == NUM_TOKENS_FROM_DATASET
            or max_tokens == NUM_TOKENS_FROM_DATASET
        ):
            # Compute number of tokens in the answer (from the input conversation)
            assistant_answer = conversation_messages[messages_to_use]
            answer_num_tokens = get_token_count(tokenizer, assistant_answer["content"])
            assert assistant_answer["role"] == "assistant"

        if min_tokens == NUM_TOKENS_FROM_DATASET:
            min_tokens = max(1, answer_num_tokens)

        if max_tokens == NUM_TOKENS_FROM_DATASET:
            max_tokens = max(1, answer_num_tokens)

    # Send the current conversation to LLM and get a response
    response: ServerResponse = await send_request(
        session,
        messages,
        req_args.chat_url,
        req_args.model,
        req_args.stream,
        min_tokens,
        max_tokens,
        req_args.timeout_sec,
    )

    if response.valid is False:
        # Request failed
        return None

    # Compute number of tokens in input / output
    input_num_tokens = get_messages_token_count(tokenizer, messages)

    # Num tokens in the user's last question
    question_num_tokens = get_token_count(tokenizer, messages[index]["content"])

    # Num tokens in the history/context of the question
    assert input_num_tokens >= question_num_tokens
    history_num_tokens = input_num_tokens - question_num_tokens

    # Num tokens in the LLM's answer (first chunk and full answer)
    first_chunk_tokens = get_token_count(tokenizer, response.first_chunk)

    output_content = response.content
    output_num_tokens = get_token_count(tokenizer, output_content)

    # Prefix caching approximated cached percent
    approx_cached_percent = (
        100.0 * (history_num_tokens / input_num_tokens) if input_num_tokens > 0 else 0.0
    )

    # Compute the correct TTFT and TPOT (based on tokens and not chunks).
    # Required because multiple output tokens may be bundled in a single chunk.
    if output_num_tokens > 1 and output_num_tokens > first_chunk_tokens:
        # More than one token and more than one chunk in the output
        decode_ms = response.latency_ms - response.ttft_ms
        decode_num_tokens = output_num_tokens - first_chunk_tokens
        tpot_ms = decode_ms / decode_num_tokens
    else:
        # In this case: output_num_tokens == first_chunk_tokens
        # Output was a single chunk (output_num_tokens > 1)
        # or even a single token (output_num_tokens == 1)
        tpot_ms = 0.0

    if first_chunk_tokens > 1:
        # First chunk had multiple tokens, adjust TTFT for a single token
        delta_ms = (first_chunk_tokens - 1) * tpot_ms
        ttft_ms = max(0.1, response.ttft_ms - delta_ms)
    else:
        # First chunk had only one token
        ttft_ms = response.ttft_ms

    rs = RequestStats(
        ttft_ms=ttft_ms,
        tpot_ms=tpot_ms,
        latency_ms=response.latency_ms,
        start_time_ms=response.start_time_ms,
        input_num_turns=len(messages),
        input_num_tokens=input_num_tokens,
        output_num_tokens=output_num_tokens,
        output_num_chunks=response.num_chunks,
        output_num_first_chunk_tokens=first_chunk_tokens,
        approx_cached_percent=approx_cached_percent,
        conversation_id=conv_id,
        client_id=client_id,
    )

    if verbose:
        print(
            f"\n{Color.YELLOW}Response ({output_num_tokens} tokens):{Color.RESET}",
            output_content,
        )
        print(f"{Color.YELLOW}Response metrics: {rs}{Color.RESET}")
        print("-" * 70)

    # Save the LLM's answer (will be used as part of the context for the next user turn)
    answer_index = messages_to_use
    if len(conversation_messages) > answer_index:
        assert conversation_messages[answer_index]["role"] == "assistant", (
            f"Failed on conversation ID {conv_id}, message role should be assistant"
        )

        orig_content = conversation_messages[answer_index]["content"]
        if verify_output:
            # Compare the new answer to the answer from the input file
            debug_info = (
                f"LLM/dataset answers do not match ({conv_id}):"
                f"\n'{get_short_string(output_content)}' (len: {len(output_content)}),"
                f"\n'{get_short_string(orig_content)}' (len: {len(orig_content)})"
            )
            if orig_content != output_content:
                raise ValueError(debug_info)

        # Update the answer
        conversation_messages[answer_index]["content"] = output_content
    else:
        # A user prompt that has no answer, add the answer as a new message
        new_answer = {"role": "assistant", "content": output_content}
        conversation_messages.append(new_answer)

    return rs