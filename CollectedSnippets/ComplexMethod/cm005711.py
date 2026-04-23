def _get_parameter_info(param_name, documented_params, source_args_dict, param_type, optional):
    """
    Get parameter documentation details from the appropriate source.
    Tensor shape, optional status and description are taken from the custom docstring in priority if available.
    Type is taken from the function signature first, then from the custom docstring if missing from the signature

    Args:
        param_name (`str`): Name of the parameter
        documented_params (`dict`): Dictionary of documented parameters (manually specified in the docstring)
        source_args_dict (`dict`): Default source args dictionary to use if not in documented_params
        param_type (`str`): Current parameter type (may be updated)
        optional (`bool`): Whether the parameter is optional (may be updated)
    """
    description = None
    shape = None
    shape_string = ""
    is_documented = True
    additional_info = None
    optional_string = r", *optional*" if optional else ""

    if param_name in documented_params:
        # Parameter is documented in the function's docstring
        if (
            param_type == ""
            and documented_params[param_name].get("type", None) is not None
            or documented_params[param_name]["additional_info"]
        ):
            param_type = documented_params[param_name]["type"]
        optional = documented_params[param_name]["optional"]
        shape = documented_params[param_name].get("shape", None)
        shape_string = shape if shape else ""
        additional_info = documented_params[param_name]["additional_info"] or ""
        description = f"{documented_params[param_name]['description']}\n"
    elif param_name in source_args_dict:
        # Parameter is documented in ModelArgs or ImageProcessorArgs
        param_type = source_args_dict[param_name].get("type", param_type)
        shape = source_args_dict[param_name].get("shape", None)
        shape_string = " " + shape if shape else ""
        description = source_args_dict[param_name]["description"]
        additional_info = source_args_dict[param_name].get("additional_info", None)
        if additional_info:
            additional_info = shape_string + optional_string + ", " + additional_info
    else:
        # Parameter is not documented
        is_documented = False

    return param_type, optional_string, shape_string, additional_info, description, is_documented