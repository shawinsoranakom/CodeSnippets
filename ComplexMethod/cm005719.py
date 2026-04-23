def _prepare_return_docstring(output_type, config_class, add_intro=True):
    """
    Prepare the return docstring from a ModelOutput class.

    This is a robust replacement for the old _prepare_output_docstrings from doc.py,
    using the same parsing and formatting methods as the rest of auto_docstring.

    Args:
        output_type: The ModelOutput class to generate documentation for
        config_class (`str`): Config class for the model
        add_intro (`bool`): Whether to add the introduction text

    Returns:
        str: Formatted return docstring
    """
    output_docstring = output_type.__doc__

    # If the class has no docstring, try to use the parent class's docstring
    if output_docstring is None and hasattr(output_type, "__mro__"):
        for base in output_type.__mro__[1:]:  # Skip the class itself
            if base.__doc__ is not None:
                output_docstring = base.__doc__
                break

    if output_docstring is None:
        if add_intro:
            raise ValueError(
                f"No docstring found for `{output_type.__name__}` or its parent classes. "
                "Make sure the ModelOutput class or one of its parents has a docstring."
            )
        return ""

    # Parse the output class docstring to extract parameters
    documented_params, _ = parse_docstring(output_docstring)

    if not documented_params and add_intro:
        raise ValueError(
            f"No `Args` or `Parameters` section is found in the docstring of `{output_type.__name__}`. "
            "Make sure it has a docstring and contains either `Args` or `Parameters`."
        )

    # Build the return section
    full_output_type, _ = process_type_annotation(output_type)
    if add_intro:
        # Import here to avoid circular import
        from .doc import PT_RETURN_INTRODUCTION

        intro = PT_RETURN_INTRODUCTION.format(full_output_type=full_output_type, config_class=config_class)
    else:
        intro = f"Returns:\n    `{full_output_type}`"
        if documented_params:
            intro += ":\n"
        else:
            intro += "\n"

    # Build the parameters section
    params_text = ""
    if documented_params:
        for param_name, param_info in documented_params.items():
            param_type = param_info.get("type", "")
            param_description = param_info.get("description", "").strip()
            additional_info = param_info.get("additional_info", "")

            # Handle types with unbalanced backticks due to nested parentheses
            # The parse_docstring function splits types like `tuple(torch.FloatTensor)` incorrectly
            # so we need to reconstruct the complete type by grabbing the closing part from additional_info
            if param_type.startswith("`") and not param_type.endswith("`"):
                # Find the closing backtick in additional_info
                closing_backtick_idx = additional_info.find("`")
                if closing_backtick_idx != -1:
                    # Grab everything up to and including the closing backtick
                    param_type += additional_info[: closing_backtick_idx + 1]
                    # Remove that part from additional_info
                    additional_info = additional_info[closing_backtick_idx + 1 :]

            # Strip backticks from type to add them back consistently
            param_type = param_type.strip("`")

            # Use process_type_annotation to ensure consistent type formatting
            # This applies the same formatting rules as the rest of auto_docstring
            if param_type:
                param_type, _ = process_type_annotation(param_type)

            # Build the parameter line
            if additional_info:
                # additional_info contains shape and optional status
                param_line = f"- **{param_name}** (`{param_type}`{additional_info}) -- {param_description}"
            else:
                param_line = f"- **{param_name}** (`{param_type}`) -- {param_description}"

            # Handle multi-line descriptions:
            # Split the description to handle continuations with proper indentation
            lines = param_line.split("\n")
            formatted_lines = []
            for i, line in enumerate(lines):
                if i == 0:
                    # First line gets no extra indent (just the bullet point)
                    formatted_lines.append(line)
                else:
                    # Continuation lines: strip existing indentation and add 2 spaces (relative to the bullet)
                    formatted_lines.append("  " + line.lstrip())

            param_text = "\n".join(formatted_lines)

            # Indent everything to 4 spaces and append with newline
            param_text_indented = set_min_indent(param_text, 4)
            params_text += param_text_indented + "\n"

    result = intro + params_text

    return result