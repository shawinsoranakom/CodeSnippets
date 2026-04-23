def _tokenise(path: str) -> list[tuple[str, str]] | None:
    """
    Convert the raw path string (starting with a delimiter) into
    [ (delimiter, identifier), … ] or None if the syntax is malformed.
    """
    tokens: list[tuple[str, str]] = []
    while path:
        # 1. Which delimiter starts this chunk?
        delim = next((d for d in DYNAMIC_DELIMITERS if path.startswith(d)), None)
        if delim is None:
            return None  # invalid syntax

        # 2. Slice off the delimiter, then up to the next delimiter (or EOS)
        path = path[len(delim) :]
        nxt_delim, pos = _next_delim(path)
        token, path = (
            path[: pos if pos != -1 else len(path)],
            path[pos if pos != -1 else len(path) :],
        )
        if token == "":
            return None  # empty identifier is invalid
        tokens.append((delim, token))
    return tokens