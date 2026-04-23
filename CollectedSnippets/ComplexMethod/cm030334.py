def parse_value(
    src: str, pos: Pos, parse_float: ParseFloat
) -> tuple[Pos, Any]:
    try:
        char: str | None = src[pos]
    except IndexError:
        char = None

    # IMPORTANT: order conditions based on speed of checking and likelihood

    # Basic strings
    if char == '"':
        if src.startswith('"""', pos):
            return parse_multiline_str(src, pos, literal=False)
        return parse_one_line_basic_str(src, pos)

    # Literal strings
    if char == "'":
        if src.startswith("'''", pos):
            return parse_multiline_str(src, pos, literal=True)
        return parse_literal_str(src, pos)

    # Booleans
    if char == "t":
        if src.startswith("true", pos):
            return pos + 4, True
    if char == "f":
        if src.startswith("false", pos):
            return pos + 5, False

    # Arrays
    if char == "[":
        return parse_array(src, pos, parse_float)

    # Inline tables
    if char == "{":
        return parse_inline_table(src, pos, parse_float)

    # Dates and times
    datetime_match = RE_DATETIME.match(src, pos)
    if datetime_match:
        try:
            datetime_obj = match_to_datetime(datetime_match)
        except ValueError as e:
            raise TOMLDecodeError("Invalid date or datetime", src, pos) from e
        return datetime_match.end(), datetime_obj
    localtime_match = RE_LOCALTIME.match(src, pos)
    if localtime_match:
        return localtime_match.end(), match_to_localtime(localtime_match)

    # Integers and "normal" floats.
    # The regex will greedily match any type starting with a decimal
    # char, so needs to be located after handling of dates and times.
    number_match = RE_NUMBER.match(src, pos)
    if number_match:
        return number_match.end(), match_to_number(number_match, parse_float)

    # Special floats
    first_three = src[pos : pos + 3]
    if first_three in {"inf", "nan"}:
        return pos + 3, parse_float(first_three)
    first_four = src[pos : pos + 4]
    if first_four in {"-inf", "+inf", "-nan", "+nan"}:
        return pos + 4, parse_float(first_four)

    raise TOMLDecodeError("Invalid value", src, pos)