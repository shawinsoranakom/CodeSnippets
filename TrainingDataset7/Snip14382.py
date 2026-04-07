def smart_bytes(s, encoding="utf-8", strings_only=False, errors="strict"):
    """
    Return a bytestring version of 's', encoded as specified in 'encoding'.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, Promise):
        # The input is the result of a gettext_lazy() call.
        return s
    return force_bytes(s, encoding, strings_only, errors)