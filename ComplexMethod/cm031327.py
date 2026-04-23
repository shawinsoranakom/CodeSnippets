def iter_display_chars(
    buffer: str,
    colors: list[ColorSpan] | None = None,
    start_index: int = 0,
) -> Iterator[StyledChar]:
    """Yield visible display characters with widths and semantic color tags.

    Note: ``colors`` is consumed in place as spans are processed -- callers
    that split a buffer across multiple calls rely on this mutation to track
    which spans have already been handled.
    """

    if not buffer:
        return

    color_idx = 0
    if colors:
        while color_idx < len(colors) and colors[color_idx].span.end < start_index:
            color_idx += 1

    active_tag = None
    if colors and color_idx < len(colors) and colors[color_idx].span.start < start_index:
        active_tag = colors[color_idx].tag

    for i, c in enumerate(buffer, start_index):
        if colors and color_idx < len(colors) and colors[color_idx].span.start == i:
            active_tag = colors[color_idx].tag

        if control := _ascii_control_repr(c):
            text = control
            width = len(control)
        elif ord(c) < 128:
            text = c
            width = 1
        elif unicodedata.category(c).startswith("C"):
            text = r"\u%04x" % ord(c)
            width = len(text)
        else:
            text = c
            width = str_width(c)

        yield StyledChar(text, width, active_tag)

        if colors and color_idx < len(colors) and colors[color_idx].span.end == i:
            color_idx += 1
            active_tag = None
            # Check if the next span starts at the same position
            if color_idx < len(colors) and colors[color_idx].span.start == i:
                active_tag = colors[color_idx].tag

    # Remove consumed spans so callers see the mutation
    if color_idx > 0 and colors:
        del colors[:color_idx]