def parse_accept_lang_header(lang_string):
    """
    Parse the value of the Accept-Language header up to a maximum length.

    The value of the header is truncated to a maximum length to avoid potential
    denial of service and memory exhaustion attacks. Excessive memory could be
    used if the raw value is very large as it would be cached due to the use of
    functools.lru_cache() to avoid repetitive parsing of common header values.
    """
    # If the header value doesn't exceed the maximum allowed length, parse it.
    if len(lang_string) <= LANGUAGE_CODE_MAX_LENGTH:
        return _parse_accept_lang_header(lang_string)

    # If there is at least one comma in the value, parse up to the last comma
    # before the max length, skipping any truncated parts at the end of the
    # header value.
    if (index := lang_string.rfind(",", 0, LANGUAGE_CODE_MAX_LENGTH)) > 0:
        return _parse_accept_lang_header(lang_string[:index])

    # Don't attempt to parse if there is only one language-range value which is
    # longer than the maximum allowed length and so truncated.
    return ()