def wrap(text, width):
    """
    A word-wrap function that preserves existing line breaks. Expects that
    existing line breaks are posix newlines.

    Preserve all white space except added line breaks consume the space on
    which they break the line.

    Don't wrap long words, thus the output text may have lines longer than
    ``width``.
    """

    wrapper = textwrap.TextWrapper(
        width=width,
        break_long_words=False,
        break_on_hyphens=False,
        replace_whitespace=False,
    )
    result = []
    for line in text.splitlines():
        wrapped = wrapper.wrap(line)
        if not wrapped:
            # If `line` contains only whitespaces that are dropped, restore it.
            result.append(line)
        else:
            result.extend(wrapped)
    if text.endswith("\n"):
        # If `text` ends with a newline, preserve it.
        result.append("")
    return "\n".join(result)