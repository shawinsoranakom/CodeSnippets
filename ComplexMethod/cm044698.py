def get_character_cell_size(character: str, unicode_version: str = "auto") -> int:
    """Get the cell size of a character.

    Args:
        character (str): A single character.
        unicode_version: Unicode version, `"auto"` to auto detect, `"latest"` for the latest unicode version.

    Returns:
        int: Number of cells (0, 1 or 2) occupied by that character.
    """
    codepoint = ord(character)
    if codepoint and codepoint < 32 or 0x07F <= codepoint < 0x0A0:
        return 0
    table = load_cell_table(unicode_version).widths

    last_entry = table[-1]
    if codepoint > last_entry[1]:
        return 1

    lower_bound = 0
    upper_bound = len(table) - 1

    while lower_bound <= upper_bound:
        index = (lower_bound + upper_bound) >> 1
        start, end, width = table[index]
        if codepoint < start:
            upper_bound = index - 1
        elif codepoint > end:
            lower_bound = index + 1
        else:
            return width
    return 1