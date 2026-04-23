def _add_return_tensors_to_docstring(func, parent_class, docstring, indent_level):
    """
    Add return_tensors parameter documentation for processor __call__ methods if not already present.

    Args:
        func (`function`): Function being processed
        parent_class (`class`): Parent class of the function
        docstring (`str`): Current docstring being built
        indent_level (`int`): Indentation level

    Returns:
        str: Updated docstring with return_tensors if applicable
    """
    # Check if this is a processor __call__ method or an image processor preprocess method
    is_processor_call = False
    is_image_processor_preprocess = False
    if func.__name__ == "__call__":
        # Check if this is a processor by inspecting class hierarchy
        is_processor_call = _is_processor_class(func, parent_class)

    if func.__name__ == "preprocess":
        is_image_processor_preprocess = _is_image_processor_class(func, parent_class)

    # If it's a processor __call__ method or an image processor preprocess method and return_tensors is not already documented
    if (is_processor_call or is_image_processor_preprocess) and "return_tensors" not in docstring:
        # Get the return_tensors documentation from ImageProcessorArgs
        source_args_dict = (
            get_args_doc_from_source(ProcessorArgs)
            if is_processor_call
            else get_args_doc_from_source(ImageProcessorArgs)
        )
        return_tensors_info = source_args_dict["return_tensors"]
        param_type = return_tensors_info.get("type", "`str` or [`~utils.TensorType`]")
        description = return_tensors_info["description"]

        # Format the parameter type
        param_type = param_type if "`" in param_type else f"`{param_type}`"

        # Format the parameter docstring
        param_docstring = f"return_tensors ({param_type}, *optional*):{description}"
        docstring += set_min_indent(param_docstring, indent_level + 8)

    return docstring