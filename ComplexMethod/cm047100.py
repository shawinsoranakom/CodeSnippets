def get_encodings(hint_encoding='utf-8'):
    warnings.warn(
        "Deprecated since Odoo 18. Mostly nonsensical as the "
        "second/third encoding it yields is latin-1 which always succeeds...",
        stacklevel=2,
        category=DeprecationWarning,
    )
    fallbacks = {
        'latin1': 'latin9',
        'iso-8859-1': 'iso8859-15',
        'iso-8859-8-i': 'iso8859-8',
        'cp1252': '1252',
    }
    if hint_encoding:
        yield hint_encoding
        if hint_encoding.lower() in fallbacks:
            yield fallbacks[hint_encoding.lower()]

    # some defaults (also taking care of pure ASCII)
    for charset in ['utf8','latin1']:
        if not hint_encoding or (charset.lower() != hint_encoding.lower()):
            yield charset

    from locale import getpreferredencoding
    prefenc = getpreferredencoding()
    if prefenc and prefenc.lower() != 'utf-8':
        yield prefenc
        prefenc = fallbacks.get(prefenc.lower())
        if prefenc:
            yield prefenc