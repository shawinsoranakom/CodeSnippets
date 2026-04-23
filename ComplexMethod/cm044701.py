def _split_text(
    text: str, cell_position: int, unicode_version: str = "auto"
) -> tuple[str, str]:
    """Split text by cell position.

    If the cell position falls within a double width character, it is converted to two spaces.

    Args:
        text: Text to split.
        cell_position Offset in cells.
        unicode_version: Unicode version, `"auto"` to auto detect, `"latest"` for the latest unicode version.

    Returns:
        Tuple to two split strings.
    """
    if cell_position <= 0:
        return "", text

    spans, cell_length = split_graphemes(text, unicode_version)

    # Guess initial offset
    offset = int((cell_position / cell_length) * len(spans))
    left_size = sum(map(_span_get_cell_len, spans[:offset]))

    while True:
        if left_size == cell_position:
            if offset >= len(spans):
                return text, ""
            split_index = spans[offset][0]
            return text[:split_index], text[split_index:]
        if left_size < cell_position:
            start, end, cell_size = spans[offset]
            if left_size + cell_size > cell_position:
                return text[:start] + " ", " " + text[end:]
            offset += 1
            left_size += cell_size
        else:  # left_size > cell_position
            start, end, cell_size = spans[offset - 1]
            if left_size - cell_size < cell_position:
                return text[:start] + " ", " " + text[end:]
            offset -= 1
            left_size -= cell_size