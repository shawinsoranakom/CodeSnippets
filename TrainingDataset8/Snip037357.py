def _get_indent(line: str) -> Optional[int]:
    """Get the number of whitespaces at the beginning of the given line.
    If the line is empty, or if it contains just whitespace and a newline,
    return None.
    """
    if _EMPTY_LINE_RE.match(line) is not None:
        return None

    match = _SPACES_RE.match(line)
    return match.end() if match is not None else 0