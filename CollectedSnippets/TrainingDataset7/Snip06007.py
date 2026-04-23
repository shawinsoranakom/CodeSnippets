def _get_group_start_end(start, end, pattern):
    # Handle nested parentheses, e.g. '^(?P<a>(x|y))/b' or '^b/((x|y)\w+)$'.
    unmatched_open_brackets, prev_char = 1, None
    for idx, val in enumerate(pattern[end:]):
        # Check for unescaped `(` and `)`. They mark the start and end of a
        # nested group.
        if val == "(" and prev_char != "\\":
            unmatched_open_brackets += 1
        elif val == ")" and prev_char != "\\":
            unmatched_open_brackets -= 1
        prev_char = val
        # If brackets are balanced, the end of the string for the current named
        # capture group pattern has been reached.
        if unmatched_open_brackets == 0:
            return start, end + idx + 1