def equals_lf(line):
    """Return True if line (a text or bytestring) equals '\n'."""
    return line == ("\n" if isinstance(line, str) else b"\n")