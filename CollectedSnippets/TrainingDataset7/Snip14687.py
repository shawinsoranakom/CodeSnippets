def blankout(src, char):
    """
    Change every non-whitespace character to the given char.
    Used in the templatize function.
    """
    return dot_re.sub(char, src)