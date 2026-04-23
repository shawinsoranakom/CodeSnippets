def replace_default_in_arg_description(description: str, default: Any) -> str:
    """
    Catches the default value in the description of an argument inside a docstring and replaces it by the value passed.

    Args:
        description (`str`): The description of an argument in a docstring to process.
        default (`Any`): The default value that would be in the docstring of that argument.

    Returns:
       `str`: The description updated with the new default value.
    """
    # Lots of docstrings have `optional` or **opational** instead of *optional* so we do this fix here.
    description = description.replace("`optional`", OPTIONAL_KEYWORD)
    description = description.replace("**optional**", OPTIONAL_KEYWORD)
    if default is inspect._empty:
        # No default, make sure the description doesn't have any either
        idx = description.find(OPTIONAL_KEYWORD)
        if idx != -1:
            description = description[:idx].rstrip()
            if description.endswith(","):
                description = description[:-1].rstrip()
    elif default is None:
        # Default None are not written, we just set `*optional*`. If there is default that is not None specified in the
        # description, we do not erase it (as sometimes we set the default to `None` because the default is a mutable
        # object).
        idx = description.find(OPTIONAL_KEYWORD)
        if idx == -1:
            description = f"{description}, {OPTIONAL_KEYWORD}"
        elif re.search(r"defaults to `?None`?", description) is not None:
            len_optional = len(OPTIONAL_KEYWORD)
            description = description[: idx + len_optional]
    else:
        str_default = None
        # For numbers we may have a default that is given by a math operation (1/255 is really popular). We don't
        # want to replace those by their actual values.
        if isinstance(default, (int, float)) and re.search("defaults to `?(.*?)(?:`|$)", description) is not None:
            # Grab the default and evaluate it.
            current_default = re.search("defaults to `?(.*?)(?:`|$)", description).groups()[0]
            if default == eval_math_expression(current_default):
                try:
                    # If it can be directly converted to the type of the default, it's a simple value
                    str_default = str(type(default)(current_default))
                except Exception:
                    # Otherwise there is a math operator so we add a code block.
                    str_default = f"`{current_default}`"
            elif isinstance(default, enum.Enum) and default.name == current_default.split(".")[-1]:
                # When the default is an Enum (this is often the case for PIL.Image.Resampling), and the docstring
                # matches the enum name, keep the existing docstring rather than clobbering it with the enum value.
                str_default = f"`{current_default}`"

        if str_default is None:
            str_default = stringify_default(default)
        # Make sure default match
        if OPTIONAL_KEYWORD not in description:
            description = f"{description}, {OPTIONAL_KEYWORD}, defaults to {str_default}"
        elif _re_parse_description.search(description) is None:
            idx = description.find(OPTIONAL_KEYWORD)
            len_optional = len(OPTIONAL_KEYWORD)
            description = f"{description[: idx + len_optional]}, defaults to {str_default}"
        else:
            description = _re_parse_description.sub(rf"*optional*, defaults to {str_default}", description)

    return description