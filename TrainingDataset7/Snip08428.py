def endswith_cr(line):
    """Return True if line (a text or bytestring) ends with '\r'."""
    return line.endswith("\r" if isinstance(line, str) else b"\r")