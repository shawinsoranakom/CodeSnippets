def _parse_google_docstring(
    docstring: str | None,
    args: list[str],
    *,
    error_on_invalid_docstring: bool = False,
) -> tuple[str, dict]:
    """Parse the function and argument descriptions from the docstring of a function.

    Assumes the function docstring follows Google Python style guide.

    Args:
        docstring: The docstring to parse.
        args: The list of argument names to extract descriptions for.
        error_on_invalid_docstring: Whether to raise an error if the docstring is
            invalid.

    Returns:
        A tuple of the function description and a dictionary of argument descriptions.
    """
    if docstring:
        docstring_blocks = docstring.split("\n\n")
        if error_on_invalid_docstring:
            filtered_annotations = {
                arg
                for arg in args
                if arg not in {"run_manager", "callbacks", "runtime", "return"}
            }
            if filtered_annotations and (
                len(docstring_blocks) < _MIN_DOCSTRING_BLOCKS
                or not any(block.startswith("Args:") for block in docstring_blocks[1:])
            ):
                msg = "Found invalid Google-Style docstring."
                raise ValueError(msg)
        descriptors = []
        args_block = None
        past_descriptors = False
        for block in docstring_blocks:
            if block.startswith("Args:"):
                args_block = block
                break
            if block.startswith(("Returns:", "Example:")):
                # Don't break in case Args come after
                past_descriptors = True
            elif not past_descriptors:
                descriptors.append(block)
            else:
                continue
        description = " ".join(descriptors).strip()
    else:
        if error_on_invalid_docstring:
            msg = "Found invalid Google-Style docstring."
            raise ValueError(msg)
        description = ""
        args_block = None
    arg_descriptions = {}
    if args_block:
        arg = None
        for line in args_block.split("\n")[1:]:
            if ":" in line:
                arg, desc = line.split(":", maxsplit=1)
                arg = arg.strip()
                arg_name, _, annotations_ = arg.partition(" ")
                if annotations_.startswith("(") and annotations_.endswith(")"):
                    arg = arg_name
                arg_descriptions[arg] = desc.strip()
            elif arg:
                arg_descriptions[arg] += " " + line.strip()
    return description, arg_descriptions