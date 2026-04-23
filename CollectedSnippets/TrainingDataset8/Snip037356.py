def _get_initial_indent(lines: Iterable[str]) -> int:
    """Return the indent of the first non-empty line in the list.
    If all lines are empty, return 0.
    """
    for line in lines:
        indent = _get_indent(line)
        if indent is not None:
            return indent

    return 0