def b64decode(s, altchars=None, validate=_NOT_SPECIFIED,
              *, padded=True, ignorechars=_NOT_SPECIFIED):
    """Decode the Base64 encoded bytes-like object or ASCII string s.

    Optional altchars must be a bytes-like object or ASCII string of length 2
    which specifies the alternative alphabet used instead of the '+' and '/'
    characters.

    If padded is false, padding in input is not required.

    The result is returned as a bytes object.  A binascii.Error is raised if
    s is incorrectly padded.

    If ignorechars is specified, it should be a byte string containing
    characters to ignore from the input.  The default value of validate is
    True if ignorechars is specified, False otherwise.

    If validate is false, characters that are neither in the normal base-64
    alphabet nor the alternative alphabet are discarded prior to the
    padding check.  If validate is true, these non-alphabet characters in
    the input result in a binascii.Error if they are not in ignorechars.
    For more information about the strict base64 check, see:

    https://docs.python.org/3.11/library/binascii.html#binascii.a2b_base64
    """
    s = _bytes_from_decode_data(s)
    if validate is _NOT_SPECIFIED:
        validate = ignorechars is not _NOT_SPECIFIED
    badchar = None
    if altchars is not None:
        altchars = _bytes_from_decode_data(altchars)
        if len(altchars) != 2:
            raise ValueError(f'invalid altchars: {altchars!r}')
        if ignorechars is _NOT_SPECIFIED:
            for b in b'+/':
                if b not in altchars and b in s:
                    badchar = b
                    break
            s = s.translate(bytes.maketrans(altchars, b'+/'))
        else:
            alphabet = binascii.BASE64_ALPHABET[:-2] + altchars
            return binascii.a2b_base64(s, strict_mode=validate,
                                       alphabet=alphabet,
                                       padded=padded, ignorechars=ignorechars)
    if ignorechars is _NOT_SPECIFIED:
        ignorechars = b''
    result = binascii.a2b_base64(s, strict_mode=validate,
                                 padded=padded, ignorechars=ignorechars)
    if badchar is not None:
        import warnings
        if validate:
            warnings.warn(f'invalid character {chr(badchar)!a} in Base64 data '
                          f'with altchars={altchars!r} and validate=True '
                          f'will be an error in future Python versions',
                          DeprecationWarning, stacklevel=2)
        else:
            warnings.warn(f'invalid character {chr(badchar)!a} in Base64 data '
                          f'with altchars={altchars!r} and validate=False '
                          f'will be discarded in future Python versions',
                          FutureWarning, stacklevel=2)
    return result