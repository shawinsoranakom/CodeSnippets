def normalize_eols(raw_contents):
    """
    Take a block of raw text that will be passed through str.splitlines() to
    get universal newlines treatment.

    Return the resulting block of text with normalized `\n` EOL sequences ready
    to be written to disk using current platform's native EOLs.
    """
    lines_list = raw_contents.splitlines()
    # Ensure last line has its EOL
    if lines_list and lines_list[-1]:
        lines_list.append("")
    return "\n".join(lines_list)