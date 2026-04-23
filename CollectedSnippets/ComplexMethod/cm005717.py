def _process_kwargs_parameters(sig, func, parent_class, documented_kwargs, indent_level, undocumented_parameters):
    """
    Process **kwargs parameters if needed.

    Args:
        sig (`inspect.Signature`): Function signature
        func (`function`): Function the parameters belong to
        parent_class (`class`): Parent class of the function
        documented_kwargs (`dict`): Dictionary of kwargs that are already documented
        indent_level (`int`): Indentation level
        undocumented_parameters (`list`): List to append undocumented parameters to

    Returns:
        tuple[str, str]: (kwargs docstring, kwargs summary line to add after return_tensors)
    """
    docstring = ""
    kwargs_summary = ""
    # Check if we need to add typed kwargs description to the docstring
    unroll_kwargs = func.__name__ in UNROLL_KWARGS_METHODS
    if not unroll_kwargs and parent_class is not None:
        # Check if the function has a parent class with unroll kwargs
        unroll_kwargs = any(
            any(unroll_kwargs_class in base.__name__ for base in parent_class.__mro__)
            for unroll_kwargs_class in UNROLL_KWARGS_CLASSES
        )
    if not unroll_kwargs:
        return docstring, kwargs_summary

    # Check if this is a processor by inspecting class hierarchy
    is_processor = _is_processor_class(func, parent_class)
    is_image_processor = _is_image_processor_class(func, parent_class)

    # Use appropriate args source based on whether it's a processor or not
    if is_processor:
        source_args_dict = get_args_doc_from_source([ImageProcessorArgs, ProcessorArgs])
    elif is_image_processor:
        source_args_dict = get_args_doc_from_source(ImageProcessorArgs)
    else:
        raise ValueError(
            f"Unrolling kwargs is not supported for {func.__name__} of {parent_class.__name__ if parent_class else 'None'} class"
        )

    # get all unpackable "kwargs" parameters
    kwargs_parameters = [
        kwargs_param
        for _, kwargs_param in sig.parameters.items()
        if kwargs_param.kind == inspect.Parameter.VAR_KEYWORD
    ]
    for kwarg_param in kwargs_parameters:
        # If kwargs not typed, skip
        if kwarg_param.annotation == inspect.Parameter.empty:
            continue

        if not hasattr(kwarg_param.annotation, "__args__") or not hasattr(
            kwarg_param.annotation.__args__[0], "__name__"
        ):
            continue

        if kwarg_param.annotation.__args__[0].__name__ not in BASIC_KWARGS_TYPES:
            # Extract documentation for kwargs
            kwargs_documentation = kwarg_param.annotation.__args__[0].__doc__
            if kwargs_documentation is not None:
                documented_kwargs = parse_docstring(kwargs_documentation)[0]
            # Process each kwarg parameter
            for param_name, param_type_annotation in kwarg_param.annotation.__args__[0].__annotations__.items():
                # Handle nested kwargs structures for processors

                if is_processor and param_name.endswith("_kwargs"):
                    # Check if this is a basic kwargs type that should be skipped
                    # Basic kwargs types are generic containers that shouldn't be documented as individual params

                    # Get the actual type (unwrap Optional if needed)
                    actual_type = param_type_annotation
                    type_name = getattr(param_type_annotation, "__name__", None)
                    if type_name is None and hasattr(param_type_annotation, "__origin__"):
                        # Handle Optional[Type] or Union cases
                        args = getattr(param_type_annotation, "__args__", ())
                        for arg in args:
                            if arg is not type(None):
                                actual_type = arg
                                type_name = getattr(arg, "__name__", None)
                                break

                    # Skip only if it's one of the basic kwargs types
                    if type_name in BASIC_KWARGS_TYPES:
                        continue

                    # Otherwise, unroll the custom typed kwargs
                    # Get the nested TypedDict's annotations
                    if hasattr(actual_type, "__annotations__"):
                        nested_kwargs_doc = getattr(actual_type, "__doc__", None)
                        documented_nested_kwargs = {}
                        if nested_kwargs_doc:
                            documented_nested_kwargs = parse_docstring(nested_kwargs_doc)[0]

                        # Only process fields that are documented in the custom kwargs class's own docstring
                        # This prevents showing too many inherited parameters
                        if not documented_nested_kwargs:
                            # No documentation in the custom kwargs class, skip unrolling
                            continue

                        # Process each field in the custom typed kwargs
                        for nested_param_name, nested_param_type in actual_type.__annotations__.items():
                            # Only document parameters that are explicitly documented in the TypedDict's docstring
                            if nested_param_name not in documented_nested_kwargs:
                                continue
                            nested_param_type_str, nested_optional = process_type_annotation(
                                nested_param_type, nested_param_name
                            )

                            # Check for default value
                            nested_param_default = ""
                            if parent_class is not None:
                                nested_param_default = str(getattr(parent_class, nested_param_name, ""))
                                nested_param_default = (
                                    f", defaults to `{nested_param_default}`" if nested_param_default != "" else ""
                                )

                            # Only use the TypedDict's own docstring, not source_args_dict
                            # This prevents pulling in too many inherited parameters
                            (
                                nested_param_type_str,
                                nested_optional_string,
                                nested_shape_string,
                                nested_additional_info,
                                nested_description,
                                nested_is_documented,
                            ) = _get_parameter_info(
                                nested_param_name,
                                documented_nested_kwargs,
                                {},  # Empty dict - only use TypedDict's own docstring
                                nested_param_type_str,
                                nested_optional,
                            )

                            # nested_is_documented should always be True here since we filter for it above
                            # Check if type is missing
                            if nested_param_type_str == "":
                                print(
                                    f"🚨 {nested_param_name} for {type_name} in file {func.__code__.co_filename} has no type"
                                )
                            nested_param_type_str = (
                                nested_param_type_str if "`" in nested_param_type_str else f"`{nested_param_type_str}`"
                            )
                            # Format the parameter docstring (KWARGS_INDICATOR distinguishes from regular args)
                            if nested_additional_info:
                                docstring += set_min_indent(
                                    f"{nested_param_name} ({nested_param_type_str}{KWARGS_INDICATOR}{nested_additional_info}):{nested_description}",
                                    indent_level + 8,
                                )
                            else:
                                docstring += set_min_indent(
                                    f"{nested_param_name} ({nested_param_type_str}{KWARGS_INDICATOR}{nested_shape_string}{nested_optional_string}{nested_param_default}):{nested_description}",
                                    indent_level + 8,
                                )

                        # Skip processing the _kwargs parameter itself since we've processed its contents
                        continue
                    else:
                        # If we can't get annotations, skip this parameter
                        continue

                if documented_kwargs and param_name not in documented_kwargs:
                    continue
                param_type, optional = process_type_annotation(param_type_annotation, param_name)

                # Check for default value
                param_default = ""
                if parent_class is not None:
                    param_default = str(getattr(parent_class, param_name, ""))
                    param_default = f", defaults to `{param_default}`" if param_default != "" else ""

                param_type, optional_string, shape_string, additional_info, description, is_documented = (
                    _get_parameter_info(param_name, documented_kwargs, source_args_dict, param_type, optional)
                )

                if is_documented:
                    # Check if type is missing
                    if param_type == "":
                        print(
                            f"[ERROR] {param_name} for {kwarg_param.annotation.__args__[0].__qualname__} in file {func.__code__.co_filename} has no type"
                        )
                    param_type = param_type if "`" in param_type else f"`{param_type}`"
                    # Format the parameter docstring (KWARGS_INDICATOR distinguishes from regular args)
                    if additional_info:
                        docstring += set_min_indent(
                            f"{param_name} ({param_type}{KWARGS_INDICATOR}{additional_info}):{description}",
                            indent_level + 8,
                        )
                    else:
                        docstring += set_min_indent(
                            f"{param_name} ({param_type}{KWARGS_INDICATOR}{shape_string}{optional_string}{param_default}):{description}",
                            indent_level + 8,
                        )
                else:
                    undocumented_parameters.append(
                        f"[ERROR] `{param_name}` is part of {kwarg_param.annotation.__args__[0].__qualname__}, but not documented. Make sure to add it to the docstring of the function in {func.__code__.co_filename}."
                    )

        # Build **kwargs summary line (added after return_tensors in _process_parameters_section)
        kwargs_annot_cls = kwarg_param.annotation.__args__[0]
        kwargs_type_name = _get_base_kwargs_class(kwargs_annot_cls).__name__
        kwargs_info = source_args_dict.get("__kwargs__", {})
        kwargs_description = kwargs_info.get(
            "description",
            "Additional keyword arguments. Model-specific parameters are listed above.",
        )
        kwargs_summary = set_min_indent(
            f"**kwargs ([`{kwargs_type_name}`], *optional*):{kwargs_description}",
            indent_level + 8,
        )

    return docstring, kwargs_summary