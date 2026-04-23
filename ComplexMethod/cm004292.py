def get_all_spans(text, max_ngram_length):
    """
    Split a text into all possible ngrams up to 'max_ngram_length'. Split points are white space and punctuation.

    Args:
      text: Text to split.
      max_ngram_length: maximal ngram length.
    Yields:
      Spans, tuples of begin-end index.
    """
    start_indexes = []
    for index, char in enumerate(text):
        if not char.isalnum():
            continue
        if index == 0 or not text[index - 1].isalnum():
            start_indexes.append(index)
        if index + 1 == len(text) or not text[index + 1].isalnum():
            for start_index in start_indexes[-max_ngram_length:]:
                yield start_index, index + 1