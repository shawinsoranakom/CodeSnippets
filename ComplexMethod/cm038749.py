def gen_prompt_decode_to_target_len(
    tokenizer: TokenizerLike,
    token_sequence: list[int],
    target_token_len: int,
    max_retry: int = 10,
    add_special_tokens: bool = False,
    rng: np.random.Generator | None = None,
) -> tuple[str, list[int], int]:
    """
    Ensure decoded-then-encoded prompt length matches the target token length.

    This function decodes an initial token sequence to text and re-encodes it
    , iteratively adjusting the token sequence length to match a target.
    This is necessary because some tokenizers do not guarantee a 1:1 mapping
    between consecutive tokens and the decoded-then-encoded sequence length.
    For example, for GPT2Tokenizer:
    [6880, 6881] -> ['Ġcalls', 'here'] ->
    [1650, 939, 486] -> ['Ġcall', 'sh', 'ere']

    Returns a tuple of the final prompt string, the adjusted token sequence,
    and the token mismatch (final_len - target_token_len) if the retry budget
    is exhausted.
    """
    remain_num_try = max_retry
    token_mismatch = 0
    while True:
        prompt = tokenizer.decode(token_sequence)
        token_sequence = tokenizer.encode(prompt, add_special_tokens=add_special_tokens)
        if remain_num_try <= 0:
            if len(token_sequence) != target_token_len:
                token_mismatch = len(token_sequence) - target_token_len
            break

        if len(token_sequence) == target_token_len:
            break
        elif len(token_sequence) < target_token_len:
            if rng is not None:
                extra_tokens = rng.integers(
                    0,
                    tokenizer.vocab_size,
                    size=target_token_len - len(token_sequence),
                ).tolist()
            else:
                extra_tokens = np.random.randint(
                    0,
                    tokenizer.vocab_size,
                    size=target_token_len - len(token_sequence),
                ).tolist()
            token_sequence.extend(extra_tokens)
        elif len(token_sequence) > target_token_len:
            token_sequence = token_sequence[:target_token_len]

        remain_num_try -= 1

    return prompt, token_sequence, token_mismatch