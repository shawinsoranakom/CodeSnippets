def decoder(conv_func):
    """
    Convert bytestrings from Python's sqlite3 interface to a regular string.
    """
    return lambda s: conv_func(s.decode())