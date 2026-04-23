def _merge_punctuations(words, tokens, indices, prepended, appended):
    """Merges punctuation tokens with neighboring words."""
    # prepend punctuations
    i = len(words) - 2
    j = len(words) - 1
    while i >= 0:
        if words[i].startswith(" ") and words[i].strip() in prepended:
            words[j] = words[i] + words[j]
            tokens[j] = tokens[i] + tokens[j]
            indices[j] = indices[i] + indices[j]
            words[i] = ""
            tokens[i] = []
            indices[i] = []
        else:
            j = i
        i -= 1

    # append punctuations
    i = 0
    j = 1
    while j < len(words):
        if not words[i].endswith(" ") and words[j] in appended:
            words[i] += words[j]
            tokens[i] += tokens[j]
            indices[i] += indices[j]
            words[j] = ""
            tokens[j] = []
            indices[j] = []
        else:
            i = j
        j += 1

    # remove elements that are now empty
    words[:] = [word for word in words if word]
    tokens[:] = [token for token in tokens if token]
    indices[:] = [idx for idx in indices if idx]