def smart_str(s, encoding="utf-8", strings_only=False, errors="strict"):
    """
    Return a string representing 's'. Treat bytestrings using the 'encoding'
    codec.

    If strings_only is True, don't convert (some) non-string-like objects.
    """
    if isinstance(s, Promise):
        # The input is the result of a gettext_lazy() call.
        return s
    return force_str(s, encoding, strings_only, errors)