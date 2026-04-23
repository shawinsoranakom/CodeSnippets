def parse_inline_table(src: str, pos: Pos, parse_float: ParseFloat) -> tuple[Pos, dict[str, Any]]:
    pos += 1
    nested_dict = NestedDict()
    flags = Flags()

    pos = skip_comments_and_array_ws(src, pos)
    if src.startswith("}", pos):
        return pos + 1, nested_dict.dict
    while True:
        pos, key, value = parse_key_value_pair(src, pos, parse_float)
        key_parent, key_stem = key[:-1], key[-1]
        if flags.is_(key, Flags.FROZEN):
            raise TOMLDecodeError(f"Cannot mutate immutable namespace {key}", src, pos)
        try:
            nest = nested_dict.get_or_create_nest(key_parent, access_lists=False)
        except KeyError:
            raise TOMLDecodeError("Cannot overwrite a value", src, pos) from None
        if key_stem in nest:
            raise TOMLDecodeError(f"Duplicate inline table key {key_stem!r}", src, pos)
        nest[key_stem] = value
        pos = skip_comments_and_array_ws(src, pos)
        c = src[pos : pos + 1]
        if c == "}":
            return pos + 1, nested_dict.dict
        if c != ",":
            raise TOMLDecodeError("Unclosed inline table", src, pos)
        pos += 1
        pos = skip_comments_and_array_ws(src, pos)
        if src.startswith("}", pos):
            return pos + 1, nested_dict.dict
        if isinstance(value, (dict, list)):
            flags.set(key, Flags.FROZEN, recursive=True)