def _parse_localename(localename):

    """ Parses the locale code for localename and returns the
        result as tuple (language code, encoding).

        The localename is normalized and passed through the locale
        alias engine. A ValueError is raised in case the locale name
        cannot be parsed.

        The language code corresponds to RFC 1766.  code and encoding
        can be None in case the values cannot be determined or are
        unknown to this implementation.

    """
    code = normalize(localename)
    if '@' in code:
        # Deal with locale modifiers
        code, modifier = code.split('@', 1)
        if modifier == 'euro' and '.' not in code:
            # Assume ISO8859-15 for @euro locales. Do note that some systems
            # may use other encodings for these locales, so this may not always
            # be correct.
            return code + '@euro', 'ISO8859-15'
    else:
        modifier = ''

    if '.' in code:
        code, encoding = code.split('.')[:2]
        if modifier:
            code += '@' + modifier
        return code, encoding
    elif code == 'C':
        return None, None
    elif code == 'UTF-8':
        # On macOS "LC_CTYPE=UTF-8" is a valid locale setting
        # for getting UTF-8 handling for text.
        return None, 'UTF-8'
    raise ValueError('unknown locale: %s' % localename)