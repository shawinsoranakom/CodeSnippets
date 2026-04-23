def _cell_len(text: str, unicode_version: str) -> int:
    """Get the cell length of a string (length as it appears in the terminal).

    Args:
        text: String to measure.
        unicode_version: Unicode version, `"auto"` to auto detect, `"latest"` for the latest unicode version.

    Returns:
        Length of string in terminal cells.
    """

    if _is_single_cell_widths(text):
        return len(text)

    # "\u200d" is zero width joiner
    # "\ufe0f" is variation selector 16
    if "\u200d" not in text and "\ufe0f" not in text:
        # Simplest case with no unicode stuff that changes the size
        return sum(
            get_character_cell_size(character, unicode_version) for character in text
        )

    cell_table = load_cell_table(unicode_version)
    total_width = 0
    last_measured_character: str | None = None

    SPECIAL = {"\u200d", "\ufe0f"}

    index = 0
    character_count = len(text)

    while index < character_count:
        character = text[index]
        if character in SPECIAL:
            if character == "\u200d":
                index += 1
            elif last_measured_character:
                total_width += last_measured_character in cell_table.narrow_to_wide
                last_measured_character = None
        else:
            if character_width := get_character_cell_size(character, unicode_version):
                last_measured_character = character
                total_width += character_width
        index += 1

    return total_width