def _convert_tokens_to_string_with_added_encoders(
    tokenizer: TokenizerLike,
    output_tokens: list[str],
    skip_special_tokens: bool,
    spaces_between_special_tokens: bool,
) -> str:
    # Adapted from
    # https://github.com/huggingface/transformers/blob/v4.28.0/src/transformers/tokenization_utils.py#L921
    # NOTE(woosuk): The following code is slow because it runs a for loop over
    # the output_tokens. In Python, running a for loop over a list can be slow
    # even when the loop body is very simple.
    # Performance improvements: avoid repeated attribute and function lookups;
    # localize frequently used objects;

    sub_texts: list[str] = []
    current_sub_text: list[str] = []
    convert_tokens_to_string = tokenizer.convert_tokens_to_string
    added_vocab_set = set(tokenizer.get_added_vocab())
    all_special_tokens = (
        set(tokenizer.all_special_tokens) if skip_special_tokens else ()
    )

    for token in output_tokens:
        # Use precomputed set for skip-special check
        if token in all_special_tokens:
            continue
        if token in added_vocab_set:
            if current_sub_text:
                sub_texts.append(convert_tokens_to_string(current_sub_text))
                current_sub_text.clear()
            sub_texts.append(token)
        else:
            current_sub_text.append(token)
    if current_sub_text:
        sub_texts.append(convert_tokens_to_string(current_sub_text))
    if spaces_between_special_tokens:
        return " ".join(sub_texts)
    return "".join(sub_texts)