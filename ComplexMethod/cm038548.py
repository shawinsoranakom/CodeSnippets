def detokenize_incrementally(
    tokenizer: TokenizerLike,
    all_input_ids: list[int],
    prev_tokens: list[str] | None,
    prefix_offset: int,
    read_offset: int,
    skip_special_tokens: bool = False,
    spaces_between_special_tokens: bool = True,
) -> tuple[list[str], str, int, int]:
    """Detokenizes the input ids incrementally and returns the new tokens
    and the new text.

    If `prev_tokens` is None, this function will convert the input ids to
    tokens and return the tokens and the new text. Otherwise, it will return the
    new tokens and the new text.

    This function will also return the new prefix offset and the new read
    offset to be used in the next iteration.

    The offsets are necessary to defeat cleanup algorithms in the decode which
    decide to add a space or not depending on the surrounding ids.

    Args:
        tokenizer: The tokenizer to use.
        all_input_ids: The input ids. The last id is the new token id.
        prev_tokens: The previous tokens. If None, this function will convert
            the input ids to tokens and return the tokens and the new text.
        prefix_offset: The prefix offset.
        read_offset: The read offset.
        skip_special_tokens: Whether to skip special tokens.
        spaces_between_special_tokens: Whether to add spaces between special
            tokens.
    """
    new_token_id = all_input_ids[-1]
    # This is the first iteration for this sequence
    is_first_iter = prev_tokens is None
    if is_first_iter:
        (prev_tokens, prefix_offset, read_offset) = convert_prompt_ids_to_tokens(
            tokenizer, all_input_ids[:-1], skip_special_tokens=skip_special_tokens
        )
    assert prev_tokens is not None

    # If the new token id is out of bounds, return an empty string.
    if 0 <= new_token_id < len(tokenizer):
        # Put new_token_id in a list so skip_special_tokens is respected
        new_tokens = tokenizer.convert_ids_to_tokens(
            [new_token_id], skip_special_tokens=skip_special_tokens
        )
        if isinstance(new_tokens, str):
            new_tokens = [new_tokens]
        else:
            # This is required to guard against out-of-vocab prompt token ids
            # (for example when using dummy weights)
            _replace_none_with_empty(new_tokens)  # type: ignore[arg-type]
    else:
        new_tokens = [""]
    output_tokens = prev_tokens + new_tokens

    # If this is the first iteration, return all tokens.
    if is_first_iter:
        new_tokens = output_tokens

    # The prefix text is necessary only to defeat cleanup algorithms in
    # the decode which decide to add a space or not depending on the
    # surrounding ids.
    if tokenizer.is_fast or not tokenizer.get_added_vocab():
        prefix_text = tokenizer.convert_tokens_to_string(
            output_tokens[prefix_offset:read_offset]
        )
        new_text = tokenizer.convert_tokens_to_string(output_tokens[prefix_offset:])
    else:
        prefix_text = _convert_tokens_to_string_with_added_encoders(
            tokenizer,
            output_tokens[prefix_offset:read_offset],
            skip_special_tokens=skip_special_tokens,
            spaces_between_special_tokens=spaces_between_special_tokens,
        )
        new_text = _convert_tokens_to_string_with_added_encoders(
            tokenizer,
            output_tokens[prefix_offset:],
            skip_special_tokens=skip_special_tokens,
            spaces_between_special_tokens=spaces_between_special_tokens,
        )

    if len(new_text) <= len(prefix_text) or new_text.endswith("�"):
        # utf-8 char at the end means it's a potential unfinished byte sequence
        # from byte fallback tokenization.
        # If it's in the middle, it's probably a real invalid id generated
        # by the model
        return new_tokens, "", prefix_offset, read_offset

    new_text = new_text[len(prefix_text) :]
    return new_tokens, new_text, read_offset, len(output_tokens)