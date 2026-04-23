def generate_new_docstring_for_class(
    lines,
    item: DecoratedItem,
    custom_args_dict,
    source: str,
):
    """
    Wrapper for class docstring generation (via __init__) using the generalized helper.
    Returns the new docstring and relevant signature/docstring indices.
    """
    # Use pre-extracted information from DecoratedItem (no need to search or re-parse!)
    if item.has_init:
        # Class has an __init__ method - use its args and body start
        sig_end_line = item.body_start_line - 1  # Convert from body start to sig end (0-based)
        args_in_signature = item.args
        output_docstring_indent = 8
        # Add ProcessorArgs for Processor classes
        if item.is_processor:
            source_args_doc = [ModelArgs, ImageProcessorArgs, ProcessorArgs]
        else:
            source_args_doc = [ModelArgs, ImageProcessorArgs]
    elif item.is_model_output:
        # ModelOutput class - extract args from dataclass attributes
        current_line_end = item.def_line - 1  # Convert to 0-based
        sig_end_line = current_line_end + 1
        docstring_end = _find_docstring_end_line(lines, sig_end_line)
        model_output_class_start = docstring_end + 1 if docstring_end is not None else sig_end_line - 1
        model_output_class_end = model_output_class_start
        while model_output_class_end < len(lines) and (
            lines[model_output_class_end].startswith("    ") or lines[model_output_class_end] == ""
        ):
            model_output_class_end += 1
        dataclass_content = lines[model_output_class_start : model_output_class_end - 1]
        args_in_signature = get_args_in_dataclass(lines, dataclass_content)
        output_docstring_indent = 4
        source_args_doc = [ModelOutputArgs]
    elif item.is_config:
        # Config class (PreTrainedConfig subclass) - args are class-level type annotations,
        # docstring is at class body level (no __init__ in source; @strict generates one at runtime).
        current_line_end = item.def_line - 1  # Convert to 0-based
        sig_end_line = current_line_end + 1
        args_in_signature = item.args
        output_docstring_indent = 4
        source_args_doc = [ConfigArgs]
    else:
        # Class has no __init__ and is not a ModelOutput or Config - nothing to document
        return "", None, None, [], [], []

    docstring_start_line = sig_end_line if '"""' in lines[sig_end_line] else None

    return generate_new_docstring_for_signature(
        lines,
        args_in_signature,
        sig_end_line,
        docstring_start_line,
        arg_indent="",
        custom_args_dict=custom_args_dict,
        output_docstring_indent=output_docstring_indent,
        source_args_doc=source_args_doc,
        is_model_output=item.is_model_output,
    )