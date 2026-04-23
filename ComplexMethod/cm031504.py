def find_paragraph(text, mark):
    """Returns the start/stop indices enclosing the paragraph that mark is in.

    Also returns the comment format string, if any, and paragraph of text
    between the start/stop indices.
    """
    lineno, col = map(int, mark.split("."))
    line = text.get("%d.0" % lineno, "%d.end" % lineno)

    # Look for start of next paragraph if the index passed in is a blank line
    while text.compare("%d.0" % lineno, "<", "end") and is_all_white(line):
        lineno = lineno + 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    first_lineno = lineno
    comment_header = get_comment_header(line)
    comment_header_len = len(comment_header)

    # Once start line found, search for end of paragraph (a blank line)
    while get_comment_header(line)==comment_header and \
              not is_all_white(line[comment_header_len:]):
        lineno = lineno + 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    last = "%d.0" % lineno

    # Search back to beginning of paragraph (first blank line before)
    lineno = first_lineno - 1
    line = text.get("%d.0" % lineno, "%d.end" % lineno)
    while lineno > 0 and \
              get_comment_header(line)==comment_header and \
              not is_all_white(line[comment_header_len:]):
        lineno = lineno - 1
        line = text.get("%d.0" % lineno, "%d.end" % lineno)
    first = "%d.0" % (lineno+1)

    return first, last, comment_header, text.get(first, last)