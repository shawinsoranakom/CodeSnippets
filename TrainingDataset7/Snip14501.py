def strip_tags(value):
    """Return the given HTML with all tags stripped."""
    value = str(value)
    for long_open_tag in long_open_tag_without_closing_re.finditer(value):
        if long_open_tag.group().count("<") >= MAX_STRIP_TAGS_DEPTH:
            raise SuspiciousOperation
    # Note: in typical case this loop executes _strip_once twice (the second
    # execution does not remove any more tags).
    strip_tags_depth = 0
    while "<" in value and ">" in value:
        if strip_tags_depth >= MAX_STRIP_TAGS_DEPTH:
            raise SuspiciousOperation
        new_value = _strip_once(value)
        if value.count("<") == new_value.count("<"):
            # _strip_once wasn't able to detect more tags.
            break
        value = new_value
        strip_tags_depth += 1
    return value