def is_binary_string(inp):
    """Guess if an input bytesarray can be encoded as a string."""
    # From https://stackoverflow.com/a/7392391
    return bool(inp.translate(None, TEXTCHARS))