def remove_non_capturing_groups(pattern):
    r"""
    Find non-capturing groups in the given `pattern` and remove them, e.g.
    1. (?P<a>\w+)/b/(?:\w+)c(?:\w+) => (?P<a>\\w+)/b/c
    2. ^(?:\w+(?:\w+))a => ^a
    3. ^a(?:\w+)/b(?:\w+) => ^a/b
    """
    group_start_end_indices = _find_groups(pattern, non_capturing_group_matcher)
    final_pattern, prev_end = "", None
    for start, end, _ in group_start_end_indices:
        final_pattern += pattern[prev_end:start]
        prev_end = end
    return final_pattern + pattern[prev_end:]