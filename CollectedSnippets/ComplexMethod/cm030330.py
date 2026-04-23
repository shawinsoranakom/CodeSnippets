def key_value_rule(
    src: str, pos: Pos, out: Output, header: Key, parse_float: ParseFloat
) -> Pos:
    pos, key, value = parse_key_value_pair(src, pos, parse_float)
    key_parent, key_stem = key[:-1], key[-1]
    abs_key_parent = header + key_parent

    relative_path_cont_keys = (header + key[:i] for i in range(1, len(key)))
    for cont_key in relative_path_cont_keys:
        # Check that dotted key syntax does not redefine an existing table
        if out.flags.is_(cont_key, Flags.EXPLICIT_NEST):
            raise TOMLDecodeError(f"Cannot redefine namespace {cont_key}", src, pos)
        # Containers in the relative path can't be opened with the table syntax or
        # dotted key/value syntax in following table sections.
        out.flags.add_pending(cont_key, Flags.EXPLICIT_NEST)

    if out.flags.is_(abs_key_parent, Flags.FROZEN):
        raise TOMLDecodeError(
            f"Cannot mutate immutable namespace {abs_key_parent}", src, pos
        )

    try:
        nest = out.data.get_or_create_nest(abs_key_parent)
    except KeyError:
        raise TOMLDecodeError("Cannot overwrite a value", src, pos) from None
    if key_stem in nest:
        raise TOMLDecodeError("Cannot overwrite a value", src, pos)
    # Mark inline table and array namespaces recursively immutable
    if isinstance(value, (dict, list)):
        out.flags.set(header + key, Flags.FROZEN, recursive=True)
    nest[key_stem] = value
    return pos