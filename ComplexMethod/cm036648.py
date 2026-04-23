def test_decode_streaming(
    tokenizer,
    truth,
    with_prompt,
    skip_special_tokens,
    spaces_between_special_tokens,
    fast,
):
    if fast and not isinstance(tokenizer, PreTrainedTokenizerFast):
        pytest.skip()

    if skip_special_tokens and not spaces_between_special_tokens:
        pytest.skip()

    if not fast and isinstance(tokenizer, PreTrainedTokenizerFast):
        # Fix up inconsistency in fast/slow tokenizer behaviour.
        tokenizer.add_special_tokens(
            {
                "additional_special_tokens": [
                    at
                    for at in tokenizer._tokenizer.get_added_tokens_decoder().values()
                    if at.special
                ]
            }
        )

    extra_decode_args = (
        {}
        if not isinstance(tokenizer, PreTrainedTokenizer)
        else {"spaces_between_special_tokens": spaces_between_special_tokens}
    )

    truth_tokens = tokenizer(truth, add_special_tokens=False).input_ids
    if tokenizer.bos_token_id is not None:
        truth_tokens.insert(0, tokenizer.bos_token_id)
    truth_tokens.append(tokenizer.eos_token_id)

    new_truth = tokenizer.decode(
        truth_tokens, skip_special_tokens=skip_special_tokens, **extra_decode_args
    )

    if with_prompt:
        num_prompt_tokens = len(
            tokenizer(truth[: len(truth) // 2], add_special_tokens=False).input_ids
        )
        if tokenizer.bos_token_id is not None:
            num_prompt_tokens += 1

        prompt_input_ids = truth_tokens[:num_prompt_tokens]
        generated_input_ids = truth_tokens[num_prompt_tokens:]
        all_input_ids = prompt_input_ids + generated_input_ids
        starting_index = len(prompt_input_ids)
        prompt = tokenizer.decode(
            prompt_input_ids,
            skip_special_tokens=skip_special_tokens,
            **extra_decode_args,
        )

        generated = new_truth[len(prompt) :]
    else:
        generated = new_truth
        starting_index = 0
        all_input_ids = truth_tokens

    decoded_text, out_ids = _run_incremental_decode(
        tokenizer,
        all_input_ids,
        skip_special_tokens=skip_special_tokens,
        starting_index=starting_index,
        spaces_between_special_tokens=spaces_between_special_tokens,
        fast=fast,
    )

    assert decoded_text == generated
    assert out_ids == all_input_ids[starting_index:]