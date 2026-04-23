def _process_regular_parameters(
    sig,
    func,
    class_name,
    documented_params,
    indent_level,
    undocumented_parameters,
    source_args_dict,
    parent_class,
    allowed_params=None,
):
    """
    Process all regular parameters (not kwargs parameters) from the function signature.

    Args:
        sig (`inspect.Signature`): Function signature
        func (`function`): Function the parameters belong to
        class_name (`str`): Name of the class
        documented_params (`dict`): Dictionary of parameters that are already documented
        indent_level (`int`): Indentation level
        undocumented_parameters (`list`): List to append undocumented parameters to
    """
    docstring = ""
    # Check if this is a processor by inspecting class hierarchy
    is_processor = _is_processor_class(func, parent_class)

    # Use appropriate args source based on whether it's a processor or not
    if source_args_dict is None:
        if is_processor:
            source_args_dict = get_args_doc_from_source([ModelArgs, ImageProcessorArgs, ProcessorArgs])
        else:
            source_args_dict = get_args_doc_from_source([ModelArgs, ImageProcessorArgs])

    missing_args = {}

    for param_name, param in sig.parameters.items():
        # Skip parameters that should be ignored
        if (
            param_name in ARGS_TO_IGNORE
            or param_name.startswith("_")  # Private/internal params (e.g. ClassVar-backed fields in configs)
            or param.kind == inspect.Parameter.VAR_POSITIONAL
            or param.kind == inspect.Parameter.VAR_KEYWORD
        ):
            continue
        # When a filter is active (e.g. config classes: only own annotations), skip inherited params
        if allowed_params is not None and param_name not in allowed_params:
            continue

        # When a filter is active (e.g. config classes: only own annotations), skip inherited params
        if allowed_params is not None and param_name not in allowed_params:
            continue

        param_name = ARGS_TO_RENAME.get(param_name, param_name)

        # Process parameter type and optional status
        param_type, optional = _process_parameter_type(param)

        # Check for default value
        param_default = ""
        if param.default != inspect._empty and param.default is not None:
            param_default = f", defaults to `{str(param.default)}`"

        param_type, optional_string, shape_string, additional_info, description, is_documented = _get_parameter_info(
            param_name, documented_params, source_args_dict, param_type, optional
        )

        if is_documented:
            if param_name == "config":
                if param_type == "":
                    param_type = f"[`{class_name}`]"
                else:
                    param_type = f"[`{param_type.split('.')[-1]}`]"
            # elif param_type == "" and False:  # TODO: Enforce typing for all parameters
            #     print(f"[ERROR] {param_name} for {func.__qualname__} in file {func.__code__.co_filename} has no type")
            param_type = param_type if "`" in param_type else f"`{param_type}`"
            # Format the parameter docstring
            if additional_info:
                param_docstring = f"{param_name} ({param_type}{additional_info}):{description}"
            else:
                param_docstring = (
                    f"{param_name} ({param_type}{shape_string}{optional_string}{param_default}):{description}"
                )
            docstring += set_min_indent(
                param_docstring,
                indent_level + 8,
            )
        else:
            missing_args[param_name] = {
                "type": param_type if param_type else "<fill_type>",
                "optional": optional,
                "shape": shape_string,
                "description": description if description else "\n    <fill_description>",
                "default": param_default,
            }
            # Try to get the correct source file; for classes decorated with @strict (huggingface_hub),
            # func.__code__.co_filename points to the wrapper in huggingface_hub, not the config file.
            try:
                if parent_class is not None:
                    _source_file = inspect.getsourcefile(parent_class) or func.__code__.co_filename
                else:
                    _source_file = inspect.getsourcefile(inspect.unwrap(func)) or func.__code__.co_filename
            except (TypeError, OSError):
                _source_file = func.__code__.co_filename
            undocumented_parameters.append(
                f"[ERROR] `{param_name}` is part of {func.__qualname__}'s signature, but not documented. Make sure to add it to the docstring of the function in {_source_file}."
            )

    return docstring, missing_args