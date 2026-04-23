def endswith_lf(line):
    """Return True if line (a text or bytestring) ends with '\n'."""
    return line.endswith("\n" if isinstance(line, str) else b"\n")