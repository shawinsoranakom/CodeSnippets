def parse_header_parameters(line, max_length=MAX_HEADER_LENGTH):
    """
    Parse a Content-type like header.
    Return the main content-type and a dictionary of options.

    If `line` is longer than `max_length`, `ValueError` is raised.
    """
    if not line:
        return "", {}

    if max_length is not None and len(line) > max_length:
        raise ValueError("Unable to parse header parameters (value too long).")

    parts = _parseparam(";" + line)
    key = parts.__next__().lower()
    pdict = {}
    for p in parts:
        i = p.find("=")
        if i >= 0:
            has_encoding = False
            name = p[:i].strip().lower()
            if name.endswith("*"):
                # Embedded lang/encoding, like "filename*=UTF-8''file.ext".
                # https://tools.ietf.org/html/rfc2231#section-4
                name = name[:-1]
                if p.count("'") == 2:
                    has_encoding = True
            value = p[i + 1 :].strip()
            if len(value) >= 2 and value[0] == value[-1] == '"':
                value = value[1:-1]
                value = value.replace("\\\\", "\\").replace('\\"', '"')
            if has_encoding:
                encoding, lang, value = value.split("'")
                value = unquote(value, encoding=encoding)
            pdict[name] = value
    return key, pdict