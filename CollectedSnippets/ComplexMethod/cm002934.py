def truncate_repetitions(text: str, min_len: int = 30) -> str:
    """
    Attempt to truncate repeating segments in the input string.

    This function looks for the longest repeating substring at the end of the input string and truncates it to appear
    only once. To be considered for removal, repetitions need to be continuous.

    Args:
        text (`str`):
            The input raw prediction to be truncated.
        min_len (int):
            The minimum length of the repeating segment.

    Returns:
        `str`: The input string with repeated segments truncated.
    """
    text_lower = text.lower()
    text_length = len(text_lower)

    if text_length < 2 * min_len:
        return text

    # try to find a length at which the tail is repeating
    max_repetition_length = None
    for repetition_length in range(min_len, int(text_length / 2)):
        # check if there is a repetition at the end
        same = True
        for i in range(0, repetition_length):
            if text_lower[text_length - repetition_length - i - 1] != text_lower[text_length - i - 1]:
                same = False
                break

        if same:
            max_repetition_length = repetition_length

    if max_repetition_length is None:
        return text

    lcs = text_lower[-max_repetition_length:]

    # remove all but the last repetition
    substituted_text = text
    substituted_text_lower = text_lower
    while substituted_text_lower.endswith(lcs):
        substituted_text = substituted_text[:-max_repetition_length]
        substituted_text_lower = substituted_text_lower[:-max_repetition_length]

    # this is the tail with the repetitions
    repeating_tail = text_lower[len(substituted_text_lower) :]

    # add until next punctuation and make sure last sentence is not repeating
    substituted_text_lower_out = substituted_text_lower
    while True:
        sentence_end = find_next_punctuation(text_lower, len(substituted_text_lower_out))
        sentence_start = find_next_punctuation(text_lower[::-1], len(substituted_text_lower_out))
        if sentence_end and sentence_start:
            sentence = text_lower[sentence_start:sentence_end]
            substituted_text_lower_out = text_lower[: sentence_end + 1]
            if sentence in repeating_tail:
                break
        else:
            break

    text_out = text[: len(substituted_text_lower_out)]

    return text_out