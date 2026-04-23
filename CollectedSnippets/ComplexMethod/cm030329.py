def loads(s: str, /, *, parse_float: ParseFloat = float) -> dict[str, Any]:
    """Parse TOML from a string."""

    # The spec allows converting "\r\n" to "\n", even in string
    # literals. Let's do so to simplify parsing.
    try:
        src = s.replace("\r\n", "\n")
    except (AttributeError, TypeError):
        raise TypeError(
            f"Expected str object, not '{type(s).__qualname__}'"
        ) from None
    pos = 0
    out = Output()
    header: Key = ()
    parse_float = make_safe_parse_float(parse_float)

    # Parse one statement at a time
    # (typically means one line in TOML source)
    while True:
        # 1. Skip line leading whitespace
        pos = skip_chars(src, pos, TOML_WS)

        # 2. Parse rules. Expect one of the following:
        #    - end of file
        #    - end of line
        #    - comment
        #    - key/value pair
        #    - append dict to list (and move to its namespace)
        #    - create dict (and move to its namespace)
        # Skip trailing whitespace when applicable.
        try:
            char = src[pos]
        except IndexError:
            break
        if char == "\n":
            pos += 1
            continue
        if char in KEY_INITIAL_CHARS:
            pos = key_value_rule(src, pos, out, header, parse_float)
            pos = skip_chars(src, pos, TOML_WS)
        elif char == "[":
            try:
                second_char: str | None = src[pos + 1]
            except IndexError:
                second_char = None
            out.flags.finalize_pending()
            if second_char == "[":
                pos, header = create_list_rule(src, pos, out)
            else:
                pos, header = create_dict_rule(src, pos, out)
            pos = skip_chars(src, pos, TOML_WS)
        elif char != "#":
            raise TOMLDecodeError("Invalid statement", src, pos)

        # 3. Skip comment
        pos = skip_comment(src, pos)

        # 4. Expect end of line or end of file
        try:
            char = src[pos]
        except IndexError:
            break
        if char != "\n":
            raise TOMLDecodeError(
                "Expected newline or end of document after a statement", src, pos
            )
        pos += 1

    return out.data.dict