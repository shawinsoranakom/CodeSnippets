def check_subword_sampling(
    tokenizer: PreTrainedTokenizer,
    text: str | None = None,
    test_sentencepiece_ignore_case: bool = True,
) -> None:
    """
    Check if the tokenizer generates different results when subword regularization is enabled.

    Subword regularization augments training data with subword sampling.
    This has a random component.

    Args:
        tokenizer: The tokenizer to check.
        text: The text to use for the checks.
        test_sentencepiece_ignore_case: See `TokenizerTesterMixin.test_sentencepiece_ignore_case`.
    """
    text = "This is a test for subword regularization." if text is None else text
    if test_sentencepiece_ignore_case:
        text = text.lower()

    tokens_list = []
    for _ in range(5):
        tokens_list.append(tokenizer.tokenize(text))

    # the list of different pairs of tokens_list
    combinations = itertools.combinations(tokens_list, 2)

    # check of sampling is done
    subword_sampling_found = False
    for combination in combinations:
        if combination[0] != combination[1]:
            subword_sampling_found = True
    unittest.TestCase().assertTrue(subword_sampling_found)

    # check if converting back to original text works
    for tokens in tokens_list:
        if test_sentencepiece_ignore_case:
            unittest.TestCase().assertEqual(text, tokenizer.convert_tokens_to_string(tokens).lower())
        else:
            unittest.TestCase().assertEqual(text, tokenizer.convert_tokens_to_string(tokens))