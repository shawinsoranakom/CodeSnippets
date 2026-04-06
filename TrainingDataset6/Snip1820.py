def is_available():
    """Returns `True` if shell logger socket available.

    :rtype: book

    """
    path = _get_socket_path()
    if not path:
        return False

    return os.path.exists(path)