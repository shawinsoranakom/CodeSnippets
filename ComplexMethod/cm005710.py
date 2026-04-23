def process_type_annotation(type_input, param_name: str | None = None) -> tuple[str, bool]:
    """
    Unified function to process and format a parameter's type annotation.

    This function intelligently handles both type objects (from inspect.Parameter.annotation)
    and string representations of types. It will:
    - Use type introspection when given a type object (preserves generic arguments)
    - Parse string representations when that's all that's available
    - Always return a formatted type string and optional flag

    Handles various type representations including:
    - Type objects with generics (e.g., list[str], Optional[int])
    - Union types (both Union[X, Y] and X | Y syntax)
    - Modern union syntax with | (e.g., "bool | None")
    - Complex typing constructs (Union, Optional, Annotated, etc.)
    - Generic types with brackets
    - Class type strings
    - Simple types and module paths

    Args:
        type_input: Either a type annotation object or a string representation of a type
        param_name (`str | None`): The parameter name (used for legacy module path handling)

    Returns:
        tuple[str, bool]: (formatted_type_string, is_optional)
    """
    optional = False

    # Path 1: Type object (best approach - preserves generic type information)
    if not isinstance(type_input, str):
        # Handle None type
        if type_input is None or type_input is type(None):
            return "None", True

        # Handle Union types and modern UnionType (X | Y)
        if get_origin(type_input) is Union or get_origin(type_input) is UnionType:
            subtypes = get_args(type_input)
            out_str = []
            for subtype in subtypes:
                if subtype is type(None):
                    optional = True
                    continue
                formatted_type = _format_type_annotation_recursive(subtype)
                out_str.append(formatted_type)

            if not out_str:
                return "", optional
            elif len(out_str) == 1:
                return out_str[0], optional
            else:
                return f"Union[{', '.join(out_str)}]", optional

        # Single type (not a Union)
        formatted_type = _format_type_annotation_recursive(type_input)
        return formatted_type, optional

    # Path 2: String representation (fallback when we only have strings)
    param_type = type_input

    # Handle Union types with | syntax
    if " | " in param_type:
        # Modern union syntax (e.g., "bool | None")
        parts = [p.strip() for p in param_type.split(" | ")]
        if "None" in parts:
            optional = True
            parts = [p for p in parts if p != "None"]
        param_type = " | ".join(parts) if parts else ""
        # Clean up module prefixes including typing
        param_type = "".join(param_type.split("typing.")).replace("transformers.", "~").replace("builtins.", "")

    elif "typing" in param_type or "Union[" in param_type or "Optional[" in param_type or "[" in param_type:
        # Complex typing construct or generic type - clean up typing module references
        param_type = "".join(param_type.split("typing.")).replace("transformers.", "~")

    elif "<class '" in param_type:
        # This is a class type like "<class 'module.ClassName'>" - should NOT append param_name
        param_type = (
            param_type.replace("transformers.", "~").replace("builtins.", "").replace("<class '", "").replace("'>", "")
        )

    else:
        # Simple type or module path - only append param_name if it looks like a module path
        # This is legacy behavior for backwards compatibility
        if param_name and "." in param_type and not param_type.split(".")[-1][0].isupper():
            # Looks like a module path ending with an attribute
            param_type = f"{param_type.replace('transformers.', '~').replace('builtins', '')}.{param_name}"
        else:
            # Simple type name, don't append param_name
            param_type = param_type.replace("transformers.", "~").replace("builtins.", "")

    # Clean up ForwardRef
    if "ForwardRef" in param_type:
        param_type = _re_forward_ref.sub(r"\1", param_type)

    # Handle Optional wrapper
    if "Optional" in param_type:
        param_type = _re_optional.sub(r"\1", param_type)
        optional = True

    return param_type, optional