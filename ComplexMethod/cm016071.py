def get_operator_range(chars_range):
    """Generates the characters from chars_range inclusive."""
    if chars_range == "None" or chars_range is None:
        return None

    if all(item not in chars_range for item in [",", "-"]):
        raise ValueError(
            "The correct format for operator_range is "
            "<start>-<end>, or <point>, <start>-<end>"
        )

    ops_start_chars_set = set()
    ranges = chars_range.split(",")
    for item in ranges:
        if len(item) == 1:
            ops_start_chars_set.add(item.lower())
            continue
        start, end = item.split("-")
        ops_start_chars_set.update(
            chr(c).lower() for c in range(ord(start), ord(end) + 1)
        )
    return ops_start_chars_set