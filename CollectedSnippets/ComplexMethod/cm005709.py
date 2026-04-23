def _format_type_annotation_recursive(type_hint):
    """
    Recursively format a type annotation object as a string, preserving generic type arguments.

    This is an internal helper used by process_type_annotation for the type object path.

    Args:
        type_hint: A type annotation object

    Returns:
        str: Formatted type string
    """
    # Handle special cases
    if type_hint is type(...) or type_hint is Ellipsis:
        return "..."
    # Note: NoneType handling is done later to preserve "NoneType" in Union[] but "None" in | syntax

    # Check if this is a generic type (e.g., list[str], dict[str, int])
    origin = get_origin(type_hint)
    args = get_args(type_hint)

    if origin is not None and args:
        # This is a generic type - format it with its arguments
        # Get the origin type name
        if hasattr(origin, "__module__") and hasattr(origin, "__name__"):
            # Clean up module name - need to handle both 'typing.' prefix and just 'typing'
            module_name = origin.__module__
            if module_name in ("typing", "types", "builtins"):
                module_name = ""
            else:
                module_name = (
                    module_name.replace("transformers.", "~")
                    .replace("typing.", "")
                    .replace("types.", "")
                    .replace("builtins.", "")
                )

            if module_name:
                origin_str = f"{module_name}.{origin.__name__}"
            else:
                origin_str = origin.__name__
        else:
            origin_str = str(origin)

        # Handle special origin types
        if origin_str == "UnionType":
            # Python 3.13's X | Y syntax - format it nicely
            arg_strs = [_format_type_annotation_recursive(arg) for arg in args]
            return " | ".join(arg_strs)

        # Special handling for Annotated[Union[...], ...] and Annotated[UnionType[...], ...]
        # Check if first arg is a Union/UnionType and format it specially
        if origin_str == "Annotated" and args:
            first_arg_origin = get_origin(args[0])
            # Check if it's a UnionType (modern | syntax) or Union (old Union[] syntax)
            if first_arg_origin is UnionType:
                # Modern union type - format as X | Y | Z (with None not NoneType)
                union_args = get_args(args[0])
                union_strs = []
                for arg in union_args:
                    if arg is type(None):
                        union_strs.append("None")  # Modern syntax uses "None"
                    else:
                        union_strs.append(_format_type_annotation_recursive(arg))
                formatted_union = " | ".join(union_strs)
                # Include the rest of the Annotated metadata
                remaining_args = [_format_type_annotation_recursive(arg) for arg in args[1:]]
                all_args = [formatted_union] + remaining_args
                return f"{origin_str}[{', '.join(all_args)}]"
            elif first_arg_origin is Union:
                # Old-style Union - format as Union[X, Y, Z]
                union_args = get_args(args[0])
                union_strs = [_format_type_annotation_recursive(arg) for arg in union_args]
                formatted_union = f"Union[{', '.join(union_strs)}]"
                # Include the rest of the Annotated metadata
                remaining_args = [_format_type_annotation_recursive(arg) for arg in args[1:]]
                all_args = [formatted_union] + remaining_args
                return f"{origin_str}[{', '.join(all_args)}]"

        # Recursively format the generic arguments
        arg_strs = [_format_type_annotation_recursive(arg) for arg in args]
        return f"{origin_str}[{', '.join(arg_strs)}]"
    elif hasattr(type_hint, "__module__") and hasattr(type_hint, "__name__"):
        # Simple type with module and name
        # Clean up module name - need to handle both 'typing.' prefix and just 'typing'
        module_name = type_hint.__module__
        if module_name in ("typing", "types", "builtins"):
            module_name = ""
        else:
            module_name = (
                module_name.replace("transformers.", "~")
                .replace("typing.", "")
                .replace("types.", "")
                .replace("builtins.", "")
            )

        if module_name:
            type_name = f"{module_name}.{type_hint.__name__}"
        else:
            type_name = type_hint.__name__

        return type_name
    else:
        # Fallback to string representation
        type_str = str(type_hint)
        # Clean up ForwardRef
        if "ForwardRef" in type_str:
            type_str = _re_forward_ref.sub(r"\1", type_str)
        # Clean up module prefixes
        type_str = type_str.replace("typing.", "").replace("types.", "")
        return type_str