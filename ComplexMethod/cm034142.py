def validate_value(target_name: str, target_ref: str, target_type: type) -> None:
        """Generate code to validate the specified value."""
        nonlocal indent

        origin_type = t.get_origin(target_type)

        if origin_type is t.ClassVar:
            return  # ignore annotations which are not fields, indicated by the t.ClassVar annotation

        allowed_types = _get_allowed_types(target_type)

        # check value

        if origin_type is t.Literal:
            # DTFIX-FUTURE: support optional literals

            values = t.get_args(target_type)

            append_line(f"""if {target_ref} not in {values}:""")
            append_line(f"""    raise ValueError(rf"{target_name} must be one of {values} instead of {{{target_ref}!r}}")""")

        allowed_refs = [register_type(allowed_type) for allowed_type in allowed_types]
        allowed_names = [repr(allowed_type) for allowed_type in allowed_types]

        if allow_subclasses:
            if len(allowed_refs) == 1:
                append_line(f"""if not isinstance({target_ref}, {allowed_refs[0]}):""")
            else:
                append_line(f"""if not isinstance({target_ref}, ({', '.join(allowed_refs)})):""")
        else:
            if len(allowed_refs) == 1:
                append_line(f"""if type({target_ref}) is not {allowed_refs[0]}:""")
            else:
                append_line(f"""if type({target_ref}) not in ({', '.join(allowed_refs)}):""")

        append_line(f"""    raise TypeError(f"{target_name} must be {' or '.join(allowed_names)} instead of {{type({target_ref})}}")""")

        # check elements (for containers)

        if target_ref.startswith('self.'):
            local_ref = target_ref[5:]
        else:
            local_ref = target_ref

        if tuple in allowed_types:
            tuple_type = _extract_type(target_type, tuple)

            idx_ref = f'{local_ref}_idx'
            item_ref = f'{local_ref}_item'
            item_name = f'{target_name}[{{{idx_ref}!r}}]'
            item_type, _ellipsis = t.get_args(tuple_type)

            if _ellipsis is not ...:
                raise ValueError(f"{cls} tuple fields must be a tuple of a single element type")

            append_line(f"""if isinstance({target_ref}, {known_types[tuple]}):""")
            append_line(f"""    for {idx_ref}, {item_ref} in enumerate({target_ref}):""")

            indent += 2
            validate_value(target_name=item_name, target_ref=item_ref, target_type=item_type)
            indent -= 2

        if list in allowed_types:
            list_type = _extract_type(target_type, list)

            idx_ref = f'{local_ref}_idx'
            item_ref = f'{local_ref}_item'
            item_name = f'{target_name}[{{{idx_ref}!r}}]'
            (item_type,) = t.get_args(list_type)

            append_line(f"""if isinstance({target_ref}, {known_types[list]}):""")
            append_line(f"""    for {idx_ref}, {item_ref} in enumerate({target_ref}):""")

            indent += 2
            validate_value(target_name=item_name, target_ref=item_ref, target_type=item_type)
            indent -= 2

        if dict in allowed_types:
            dict_type = _extract_type(target_type, dict)

            key_ref, value_ref = f'{local_ref}_key', f'{local_ref}_value'
            key_type, value_type = t.get_args(dict_type)
            key_name, value_name = f'{target_name!r} key {{{key_ref}!r}}', f'{target_name}[{{{key_ref}!r}}]'

            append_line(f"""if isinstance({target_ref}, {known_types[dict]}):""")
            append_line(f"""    for {key_ref}, {value_ref} in {target_ref}.items():""")

            indent += 2
            validate_value(target_name=key_name, target_ref=key_ref, target_type=key_type)
            validate_value(target_name=value_name, target_ref=value_ref, target_type=value_type)
            indent -= 2