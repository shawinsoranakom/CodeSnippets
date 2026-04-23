def get_bad_words_logits_processors(
    bad_words: list[str], tokenizer: TokenizerLike
) -> list[LogitsProcessor]:
    bad_words_ids: list[list[int]] = list()

    for bad_word in bad_words:
        # To prohibit words both at the beginning
        # and in the middle of text
        # (related to add_prefix_space tokenizer parameter)
        for add_prefix_space in [False, True]:
            prefix = " " if add_prefix_space else ""
            prompt = prefix + bad_word.lstrip()

            prompt_token_ids = tokenizer.encode(text=prompt, add_special_tokens=False)

            # If no space at the beginning
            # or if prefix space produces a new word token
            if (not add_prefix_space) or (
                add_prefix_space
                and prompt_token_ids[0] != bad_words_ids[-1][0]
                and len(prompt_token_ids) == len(bad_words_ids[-1])
            ):
                bad_words_ids.append(prompt_token_ids)

    return [NoBadWordsLogitsProcessor(bad_words_ids=bad_words_ids)]