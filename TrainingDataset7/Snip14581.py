def next_char(input_iter):
    r"""
    An iterator that yields the next character from "pattern_iter", respecting
    escape sequences. An escaped character is replaced by a representative of
    its class (e.g. \w -> "x"). If the escaped character is one that is
    skipped, it is not returned (the next character is returned instead).

    Yield the next character, along with a boolean indicating whether it is a
    raw (unescaped) character or not.
    """
    for ch in input_iter:
        if ch != "\\":
            yield ch, False
            continue
        ch = next(input_iter)
        representative = ESCAPE_MAPPINGS.get(ch, ch)
        if representative is None:
            continue
        yield representative, True