def vfsopen(obj, mode='r', buffering=-1, encoding=None, errors=None,
            newline=None):
    """
    Open the file pointed to by this path and return a file object, as
    the built-in open() function does.

    Unlike the built-in open() function, this function additionally accepts
    'openable' objects, which are objects with any of these special methods:

        __open_reader__()
        __open_writer__(mode)
        __open_updater__(mode)

    '__open_reader__' is called for 'r' mode; '__open_writer__' for 'a', 'w'
    and 'x' modes; and '__open_updater__' for 'r+' and 'w+' modes. If text
    mode is requested, the result is wrapped in an io.TextIOWrapper object.
    """
    if buffering != -1:
        raise ValueError("buffer size can't be customized")
    text = 'b' not in mode
    if text:
        # Call io.text_encoding() here to ensure any warning is raised at an
        # appropriate stack level.
        encoding = text_encoding(encoding)
    try:
        return open(obj, mode, buffering, encoding, errors, newline)
    except TypeError:
        pass
    if not text:
        if encoding is not None:
            raise ValueError("binary mode doesn't take an encoding argument")
        if errors is not None:
            raise ValueError("binary mode doesn't take an errors argument")
        if newline is not None:
            raise ValueError("binary mode doesn't take a newline argument")
    mode = ''.join(sorted(c for c in mode if c not in 'bt'))
    if mode == 'r':
        stream = _open_reader(obj)
    elif mode in ('a', 'w', 'x'):
        stream = _open_writer(obj, mode)
    elif mode in ('+r', '+w'):
        stream = _open_updater(obj, mode[1])
    else:
        raise ValueError(f'invalid mode: {mode}')
    if text:
        stream = TextIOWrapper(stream, encoding, errors, newline)
    return stream