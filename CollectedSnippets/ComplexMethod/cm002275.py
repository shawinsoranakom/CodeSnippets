def generate_new_docstring_for_signature(
    lines,
    args_in_signature,
    sig_end_line,
    docstring_start_line,
    arg_indent="    ",
    output_docstring_indent=8,
    custom_args_dict={},
    source_args_doc=[ModelArgs, ImageProcessorArgs],
    is_model_output=False,
):
    """
    Generalized docstring generator for a function or class signature.
    Args:
        lines: List of lines from the file.
        sig_start_line: Line index where the signature starts.
        sig_end_line: Line index where the signature ends.
        docstring_line: Line index where the docstring starts (or None if not present).
        arg_indent: Indentation for missing argument doc entries.
        is_model_output: Whether this is a ModelOutput dataclass (inherited args should be kept)
    Returns:
        new_docstring, sig_end_line, docstring_end (last docstring line index)
    """
    # Extract and clean signature
    missing_docstring_args = []
    docstring_args_ro_remove = []
    fill_docstring_args = []

    # Parse docstring if present
    args_docstring_dict = {}
    remaining_docstring = ""
    if docstring_start_line is not None:
        docstring_end_line = _find_docstring_end_line(lines, docstring_start_line)
        docstring_content = lines[docstring_start_line : docstring_end_line + 1]
        raw_doc = _normalize_docstring_code_fences("\n".join(docstring_content))
        parsed_docstring, remaining_docstring = parse_docstring(raw_doc)
        args_docstring_dict.update(parsed_docstring)
    else:
        docstring_end_line = None

    # Remove pre-existing entries for *args and untyped **kwargs from the docstring
    # (No longer needed since *args are excluded from args_in_signature)

    # Remove args that are the same as the ones in the source args doc OR have placeholders
    for arg in args_docstring_dict:
        if arg in get_args_doc_from_source(source_args_doc) and arg not in ALWAYS_OVERRIDE:
            source_arg_doc = get_args_doc_from_source(source_args_doc)[arg]
            arg_doc = args_docstring_dict[arg]

            # Check if this arg has placeholders
            has_placeholder = "<fill_type>" in arg_doc.get("type", "") or "<fill_docstring>" in arg_doc.get(
                "description", ""
            )

            # Remove if has placeholder (source will provide the real doc)
            if has_placeholder:
                docstring_args_ro_remove.append(arg)
            # Or remove if description matches source exactly
            elif source_arg_doc["description"].strip("\n ") == arg_doc["description"].strip("\n "):
                if source_arg_doc.get("shape") is not None and arg_doc.get("shape") is not None:
                    if source_arg_doc.get("shape").strip("\n ") == arg_doc.get("shape").strip("\n "):
                        docstring_args_ro_remove.append(arg)
                elif source_arg_doc.get("additional_info") is not None and arg_doc.get("additional_info") is not None:
                    if source_arg_doc.get("additional_info").strip("\n ") == arg_doc.get("additional_info").strip(
                        "\n "
                    ):
                        docstring_args_ro_remove.append(arg)
                else:
                    docstring_args_ro_remove.append(arg)

    # For regular methods/functions (not ModelOutput), also remove args not in signature
    if not is_model_output:
        for arg in list(args_docstring_dict.keys()):
            if (
                arg not in args_in_signature
                and arg not in get_args_doc_from_source(source_args_doc)
                and arg not in custom_args_dict
            ):
                docstring_args_ro_remove.append(arg)

    args_docstring_dict = {
        arg: args_docstring_dict[arg] for arg in args_docstring_dict if arg not in docstring_args_ro_remove
    }

    # Fill missing args (only when the item carries an explicit @auto_docstring decorator)
    for arg in args_in_signature:
        if (
            arg not in args_docstring_dict
            and arg not in get_args_doc_from_source(source_args_doc)
            and arg not in custom_args_dict
        ):
            missing_docstring_args.append(arg)
            args_docstring_dict[arg] = {
                "type": "<fill_type>",
                "optional": False,
                "shape": None,
                "description": "\n    <fill_docstring>",
                "default": None,
                "additional_info": None,
            }

    # Handle docstring of inherited args (for dataclasses like ModelOutput)
    # For regular methods, this will be empty since we removed args not in signature above
    ordered_args_docstring_dict = OrderedDict(
        (arg, args_docstring_dict[arg]) for arg in args_docstring_dict if arg not in args_in_signature
    )
    # Add args in the order of the signature
    ordered_args_docstring_dict.update(
        (arg, args_docstring_dict[arg]) for arg in args_in_signature if arg in args_docstring_dict
    )
    # Build new docstring
    new_docstring = ""
    if len(ordered_args_docstring_dict) > 0 or remaining_docstring:
        new_docstring += 'r"""\n'
        for arg in ordered_args_docstring_dict:
            additional_info = ordered_args_docstring_dict[arg]["additional_info"] or ""
            custom_arg_description = ordered_args_docstring_dict[arg]["description"]
            if "<fill_docstring>" in custom_arg_description and arg not in missing_docstring_args:
                fill_docstring_args.append(arg)
            if custom_arg_description.endswith('"""'):
                custom_arg_description = "\n".join(custom_arg_description.split("\n")[:-1])
            new_docstring += (
                f"{arg} ({ordered_args_docstring_dict[arg]['type']}{additional_info}):{custom_arg_description}\n"
            )
        close_docstring = True
        if remaining_docstring:
            if remaining_docstring.endswith('"""'):
                close_docstring = False
            end_docstring = "\n" if close_docstring else ""
            new_docstring += f"{set_min_indent(remaining_docstring, 0)}{end_docstring}"
        if close_docstring:
            new_docstring += '"""'
        new_docstring = set_min_indent(new_docstring, output_docstring_indent)

    return (
        new_docstring,
        sig_end_line,
        docstring_end_line if docstring_end_line is not None else sig_end_line - 1,
        missing_docstring_args,
        fill_docstring_args,
        docstring_args_ro_remove,
    )