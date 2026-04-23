def match_docstring_with_signature(obj: Any) -> tuple[str, str] | None:
    """
    Matches the docstring of an object with its signature.

    Args:
        obj (`Any`): The object to process.

    Returns:
        `Optional[Tuple[str, str]]`: Returns `None` if there is no docstring or no parameters documented in the
        docstring, otherwise returns a tuple of two strings: the current documentation of the arguments in the
        docstring and the one matched with the signature.
    """
    if len(getattr(obj, "__doc__", "")) == 0:
        # Nothing to do, there is no docstring.
        return

    # Read the docstring in the source code to see if there is a special command to ignore this object.
    try:
        source, _ = inspect.getsourcelines(obj)
    except OSError:
        source = []

    # Find the line where the docstring starts
    idx = 0
    while idx < len(source) and '"""' not in source[idx]:
        idx += 1

    ignore_order = False
    if idx < len(source):
        line_before_docstring = source[idx - 1]
        # Match '# no-format' (allowing surrounding whitespaces)
        if re.search(r"^\s*#\s*no-format\s*$", line_before_docstring):
            # This object is ignored by the auto-docstring tool
            return
        # Match '# ignore-order' (allowing surrounding whitespaces)
        elif re.search(r"^\s*#\s*ignore-order\s*$", line_before_docstring):
            ignore_order = True

    # Read the signature. Skip on `TypedDict` objects for now. Inspect cannot
    # parse their signature ("no signature found for builtin type <class 'dict'>")
    if issubclass(obj, dict) and hasattr(obj, "__annotations__"):
        return

    signature = inspect.signature(obj).parameters

    obj_doc_lines = obj.__doc__.split("\n")
    # Get to the line where we start documenting arguments
    idx = 0
    while idx < len(obj_doc_lines) and _re_args.search(obj_doc_lines[idx]) is None:
        idx += 1

    if idx == len(obj_doc_lines):
        # Nothing to do, no parameters are documented.
        return

    if "kwargs" in signature and signature["kwargs"].annotation != inspect._empty:
        # Inspecting signature with typed kwargs is not supported yet.
        return

    indent = find_indent(obj_doc_lines[idx])
    arguments = {}
    current_arg = None
    idx += 1
    start_idx = idx
    # Keep going until the arg section is finished (nonempty line at the same indent level) or the end of the docstring.
    while idx < len(obj_doc_lines) and (
        len(obj_doc_lines[idx].strip()) == 0 or find_indent(obj_doc_lines[idx]) > indent
    ):
        if find_indent(obj_doc_lines[idx]) == indent + 4:
            # New argument -> let's generate the proper doc for it
            re_search_arg = _re_parse_arg.search(obj_doc_lines[idx])
            if re_search_arg is not None:
                _, name, description = re_search_arg.groups()
                current_arg = name
                if name in signature:
                    default = signature[name].default
                    if signature[name].kind is inspect._ParameterKind.VAR_KEYWORD:
                        default = None
                    new_description = replace_default_in_arg_description(description, default)
                else:
                    new_description = description
                init_doc = _re_parse_arg.sub(rf"\1\2 ({new_description}):", obj_doc_lines[idx])
                arguments[current_arg] = [init_doc]
        elif current_arg is not None:
            arguments[current_arg].append(obj_doc_lines[idx])

        idx += 1

    # We went too far by one (perhaps more if there are a lot of new lines)
    idx -= 1
    if current_arg:
        while len(obj_doc_lines[idx].strip()) == 0:
            arguments[current_arg] = arguments[current_arg][:-1]
            idx -= 1
    # And we went too far by one again.
    idx += 1

    old_doc_arg = "\n".join(obj_doc_lines[start_idx:idx])

    old_arguments = list(arguments.keys())
    arguments = {name: "\n".join(doc) for name, doc in arguments.items()}
    # Add missing arguments with a template
    for name in set(signature.keys()) - set(arguments.keys()):
        arg = signature[name]
        # We ignore private arguments or *args/**kwargs (unless they are documented by the user)
        if name.startswith("_") or arg.kind in [
            inspect._ParameterKind.VAR_KEYWORD,
            inspect._ParameterKind.VAR_POSITIONAL,
        ]:
            arguments[name] = ""
        else:
            arg_desc = get_default_description(arg)
            arguments[name] = " " * (indent + 4) + f"{name} ({arg_desc}): <fill_docstring>"

    # Arguments are sorted by the order in the signature unless a special comment is put.
    if ignore_order:
        new_param_docs = [arguments[name] for name in old_arguments if name in signature]
        missing = set(signature.keys()) - set(old_arguments)
        new_param_docs.extend([arguments[name] for name in missing if len(arguments[name]) > 0])
    else:
        new_param_docs = [arguments[name] for name in signature if len(arguments[name]) > 0]
    new_doc_arg = "\n".join(new_param_docs)

    return old_doc_arg, new_doc_arg