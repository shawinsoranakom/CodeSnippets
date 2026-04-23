def parse_docstring(docstring, max_indent_level=0, return_intro=False):
    """
    Parse the docstring to extract the Args section and return it as a dictionary.
    The docstring is expected to be in the format:
    Args:
        arg1 (type):
            Description of arg1.
        arg2 (type):
            Description of arg2.

    # This function will also return the remaining part of the docstring after the Args section.
    Returns:/Example:
    ...
    """
    match = _re_example_or_return.search(docstring)
    if match:
        remainder_docstring = docstring[match.start() :]
        docstring = docstring[: match.start()]
    else:
        remainder_docstring = ""

    args_match = _re_args_section.search(docstring)
    # still try to find args description in the docstring, if args are not preceded by "Args:"
    docstring_intro = None
    if args_match:
        docstring_intro = docstring[: args_match.start()]
        if docstring_intro.split("\n")[-1].strip() == '"""':
            docstring_intro = "\n".join(docstring_intro.split("\n")[:-1])
        if docstring_intro.split("\n")[0].strip() == 'r"""' or docstring_intro.split("\n")[0].strip() == '"""':
            docstring_intro = "\n".join(docstring_intro.split("\n")[1:])
        if docstring_intro.strip() == "":
            docstring_intro = None
    args_section = args_match.group(1).lstrip("\n") if args_match else docstring
    if args_section.split("\n")[-1].strip() == '"""':
        args_section = "\n".join(args_section.split("\n")[:-1])
    if args_section.split("\n")[0].strip() == 'r"""' or args_section.split("\n")[0].strip() == '"""':
        args_section = "\n".join(args_section.split("\n")[1:])
    args_section = set_min_indent(args_section, 0)
    params = {}
    if args_section:
        # Use the pre-compiled pattern (max_indent_level is always 0 at all call
        # sites; if a non-zero value is ever needed, compile a fresh pattern).
        if max_indent_level == 0:
            param_pattern = _re_param
        else:
            param_pattern = re.compile(
                # |--- Group 1 ---|| Group 2 ||- Group 3 -||---------- Group 4 ----------|
                rf"^\s{{0,{max_indent_level}}}(\w+)\s*\(\s*([^, \)]*)(\s*.*?)\s*\)\s*:\s*((?:(?!\n^\s{{0,{max_indent_level}}}\w+\s*\().)*)",
                re.DOTALL | re.MULTILINE,
            )
        for match in param_pattern.finditer(args_section):
            param_name = match.group(1)
            param_type = match.group(2)
            additional_info = match.group(3)
            optional = "optional" in additional_info
            shape = parse_shape(additional_info)
            default = parse_default(additional_info)
            param_description = match.group(4).strip()
            # indent the first line of param_description to 4 spaces:
            param_description = " " * 4 + param_description
            param_description = f"\n{param_description}"
            params[param_name] = {
                "type": param_type,
                "description": param_description,
                "optional": optional,
                "shape": shape,
                "default": default,
                "additional_info": additional_info,
            }

    if params and remainder_docstring:
        remainder_docstring = "\n" + remainder_docstring

    remainder_docstring = set_min_indent(remainder_docstring, 0)

    if return_intro:
        return params, remainder_docstring, docstring_intro
    return params, remainder_docstring