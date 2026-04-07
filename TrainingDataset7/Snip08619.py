def get_str_from_wsgi(environ, key, default):
    """
    Get a value from the WSGI environ dictionary as str.

    key and default should be str objects.
    """
    value = get_bytes_from_wsgi(environ, key, default)
    return value.decode(errors="replace")