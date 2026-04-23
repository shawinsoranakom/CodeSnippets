def normalize_newlines(text):
    """Normalize CRLF and CR newlines to just LF."""
    return re_newlines.sub("\n", str(text))