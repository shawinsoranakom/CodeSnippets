def get_bytes_from_wsgi(environ, key, default):
    """
    Get a value from the WSGI environ dictionary as bytes.

    key and default should be strings.
    """
    value = environ.get(key, default)
    # Non-ASCII values in the WSGI environ are arbitrarily decoded with
    # ISO-8859-1. This is wrong for Django websites where UTF-8 is the default.
    # Re-encode to recover the original bytestring.
    return value.encode("iso-8859-1")