def _tokenize_prompts_with_image_and_batch(
    tokenizer,
    prompts: list[list[str]],
    scale_factors: list[list["torch.Tensor"]] | None,
    max_tokens_to_generate: int,
    max_position_embeddings: int,
    add_BOS: bool,  # Same issue with types as above
    add_beginning_of_answer_token: bool,
) -> tuple["torch.Tensor", "torch.Tensor"]:
    """
    Given a set of prompts and number of tokens to generate:
    - tokenize prompts
    - set the sequence length to be the max of length of prompts plus the number of tokens we would like to generate
    - pad all the sequences to this length so we can convert them into a 3D tensor.
    """

    # If not tool use, transform the coordinates while tokenizing
    if scale_factors is not None:
        transformed_prompt_tokens = []
        for prompt_seq, scale_factor_seq in zip(prompts, scale_factors):
            transformed_prompt_tokens.append(
                [
                    _transform_coordinates_and_tokenize(prompt, scale_factor.item(), tokenizer)
                    for prompt, scale_factor in zip(prompt_seq, scale_factor_seq)
                ]
            )
    else:
        transformed_prompt_tokens = [[tokenizer.tokenize(prompt) for prompt in prompt_seq] for prompt_seq in prompts]

    prompts_tokens = transformed_prompt_tokens

    if add_BOS:
        bos_token = tokenizer.vocab["<s>"]
    else:
        bos_token = tokenizer.vocab["|ENDOFTEXT|"]
    prompts_tokens = [[[bos_token] + x for x in prompt_seq] for prompt_seq in prompts_tokens]
    if add_beginning_of_answer_token:
        beginning_of_answer = tokenizer.vocab[BEGINNING_OF_ANSWER_STRING]
        # Only add bbox open token to the last subsequence since that is what will be completed
        for token_seq in prompts_tokens:
            token_seq[-1].append(beginning_of_answer)

    # Now we have a list of list of tokens which each list has a different
    # size. We want to extend this list to:
    #   - incorporate the tokens that need to be generated
    #   - make all the sequences equal length.
    # Get the prompts length.

    prompts_length = [[len(x) for x in prompts_tokens_seq] for prompts_tokens_seq in prompts_tokens]
    # Get the max prompts length.
    max_prompt_len: int = np.max(prompts_length)
    # Number of tokens in the each sample of the batch.
    samples_length = min(max_prompt_len + max_tokens_to_generate, max_position_embeddings)
    if max_prompt_len + max_tokens_to_generate > max_position_embeddings:
        logger.warning(
            f"Max subsequence prompt length of {max_prompt_len} + max tokens to generate {max_tokens_to_generate}",
            f"exceeds context length of {max_position_embeddings}. Will generate as many tokens as possible.",
        )
    # Now update the list of list to be of the same size: samples_length.
    for prompt_tokens_seq, prompts_length_seq in zip(prompts_tokens, prompts_length):
        for prompt_tokens, prompt_length in zip(prompt_tokens_seq, prompts_length_seq):
            if len(prompt_tokens) > samples_length:
                raise ValueError("Length of subsequence prompt exceeds sequence length.")
            padding_size = samples_length - prompt_length
            prompt_tokens.extend([tokenizer.vocab["|ENDOFTEXT|"]] * padding_size)

    # Now we are in a structured format, we can convert to tensors.
    prompts_tokens_tensor = torch.tensor(prompts_tokens, dtype=torch.int64)
    prompts_length_tensor = torch.tensor(prompts_length, dtype=torch.int64)

    return prompts_tokens_tensor, prompts_length_tensor