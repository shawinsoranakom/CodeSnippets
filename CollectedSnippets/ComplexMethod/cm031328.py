def disp_str(
    buffer: str,
    colors: list[ColorSpan] | None = None,
    start_index: int = 0,
    force_color: bool = False,
) -> tuple[CharBuffer, CharWidths]:
    r"""Decompose the input buffer into a printable variant with applied colors.

    Returns a tuple of two lists:
    - the first list is the input buffer, character by character, with color
      escape codes added (while those codes contain multiple ASCII characters,
      each code is considered atomic *and is attached for the corresponding
      visible character*);
    - the second list is the visible width of each character in the input
      buffer.

    Note on colors:
    - The `colors` list, if provided, is partially consumed within. We're using
      a list and not a generator since we need to hold onto the current
      unfinished span between calls to disp_str in case of multiline strings.
    - The `colors` list is computed from the start of the input block. `buffer`
      is only a subset of that input block, a single line within. This is why
      we need `start_index` to inform us which position is the start of `buffer`
      actually within user input. This allows us to match color spans correctly.

    Examples:
    >>> utils.disp_str("a = 9")
    (['a', ' ', '=', ' ', '9'], [1, 1, 1, 1, 1])

    >>> line = "while 1:"
    >>> colors = list(utils.gen_colors(line))
    >>> utils.disp_str(line, colors=colors)
    (['\x1b[1;34mw', 'h', 'i', 'l', 'e\x1b[0m', ' ', '1', ':'], [1, 1, 1, 1, 1, 1, 1, 1])

    """
    styled_chars = list(iter_display_chars(buffer, colors, start_index))
    chars: CharBuffer = []
    char_widths: CharWidths = []
    theme = THEME(force_color=force_color)

    for index, styled_char in enumerate(styled_chars):
        previous_tag = styled_chars[index - 1].tag if index else None
        next_tag = styled_chars[index + 1].tag if index + 1 < len(styled_chars) else None
        prefix = theme[styled_char.tag] if styled_char.tag and styled_char.tag != previous_tag else ""
        suffix = theme.reset if styled_char.tag and styled_char.tag != next_tag else ""
        chars.append(prefix + styled_char.text + suffix)
        char_widths.append(styled_char.width)

    return chars, char_widths