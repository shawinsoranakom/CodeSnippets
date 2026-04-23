def parse_basic_str(src: str, pos: Pos, *, multiline: bool) -> tuple[Pos, str]:
    if multiline:
        error_on = ILLEGAL_MULTILINE_BASIC_STR_CHARS
        parse_escapes = parse_basic_str_escape_multiline
    else:
        error_on = ILLEGAL_BASIC_STR_CHARS
        parse_escapes = parse_basic_str_escape
    result = ""
    start_pos = pos
    while True:
        try:
            char = src[pos]
        except IndexError:
            raise TOMLDecodeError("Unterminated string", src, pos) from None
        if char == '"':
            if not multiline:
                return pos + 1, result + src[start_pos:pos]
            if src.startswith('"""', pos):
                return pos + 3, result + src[start_pos:pos]
            pos += 1
            continue
        if char == "\\":
            result += src[start_pos:pos]
            pos, parsed_escape = parse_escapes(src, pos)
            result += parsed_escape
            start_pos = pos
            continue
        if char in error_on:
            raise TOMLDecodeError(f"Illegal character {char!r}", src, pos)
        pos += 1