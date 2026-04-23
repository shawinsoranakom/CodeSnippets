def _prepare_output_docstrings(output_type, config_class, min_indent=None, add_intro=True):
    """
    Prepares the return part of the docstring using `output_type`.
    """
    output_docstring = output_type.__doc__
    params_docstring = None
    if output_docstring is not None:
        # Remove the head of the docstring to keep the list of args only
        lines = output_docstring.split("\n")
        i = 0
        while i < len(lines) and re.search(r"^\s*(Args|Parameters):\s*$", lines[i]) is None:
            i += 1
        if i < len(lines):
            params_docstring = "\n".join(lines[(i + 1) :])
            params_docstring = _convert_output_args_doc(params_docstring)
        elif add_intro:
            raise ValueError(
                f"No `Args` or `Parameters` section is found in the docstring of `{output_type.__name__}`. Make sure it has "
                "docstring and contain either `Args` or `Parameters`."
            )

    # Add the return introduction
    if add_intro:
        full_output_type = f"{output_type.__module__}.{output_type.__name__}"
        intro = PT_RETURN_INTRODUCTION.format(full_output_type=full_output_type, config_class=config_class)
    else:
        full_output_type = str(output_type)
        intro = f"\nReturns:\n    `{full_output_type}`"
        if params_docstring is not None:
            intro += ":\n"

    result = intro
    if params_docstring is not None:
        result += params_docstring

    # Apply minimum indent if necessary
    if min_indent is not None:
        lines = result.split("\n")
        # Find the indent of the first nonempty line
        i = 0
        while len(lines[i]) == 0:
            i += 1
        indent = len(_get_indent(lines[i]))
        # If too small, add indentation to all nonempty lines
        if indent < min_indent:
            to_add = " " * (min_indent - indent)
            lines = [(f"{to_add}{line}" if len(line) > 0 else line) for line in lines]
            result = "\n".join(lines)

    return result