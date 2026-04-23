def get_text_width(text: str) -> int:
    """Function that utilizes ``wcswidth`` or ``wcwidth`` to determine the
    number of columns used to display a text string.

    We try first with ``wcswidth``, and fallback to iterating each
    character and using wcwidth individually, falling back to a value of 0
    for non-printable wide characters.
    """
    if not isinstance(text, str):
        raise TypeError('get_text_width requires text, not %s' % type(text))

    try:
        width = _LIBC.wcswidth(text, _MAX_INT)
    except ctypes.ArgumentError:
        width = -1
    if width != -1:
        return width

    width = 0
    counter = 0
    for c in text:
        counter += 1
        if c in (u'\x08', u'\x7f', u'\x94', u'\x1b'):
            # A few characters result in a subtraction of length:
            # BS, DEL, CCH, ESC
            # ESC is slightly different in that it's part of an escape sequence, and
            # while ESC is non printable, it's part of an escape sequence, which results
            # in a single non printable length
            width -= 1
            counter -= 1
            continue

        try:
            w = _LIBC.wcwidth(c)
        except ctypes.ArgumentError:
            w = -1
        if w == -1:
            # -1 signifies a non-printable character
            # use 0 here as a best effort
            w = 0
        width += w

    if width == 0 and counter:
        raise EnvironmentError(
            'get_text_width could not calculate text width of %r' % text
        )

    # It doesn't make sense to have a negative printable width
    return width if width >= 0 else 0