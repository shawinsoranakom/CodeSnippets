def parse_return(annotation, error_fn):
    if annotation is None:
        return "()"

    if annotation is inspect.Parameter.empty:
        error_fn("No return type annotation was provided. Please add one.")

    origin = typing.get_origin(annotation)
    if origin is not tuple:
        if annotation not in SUPPORTED_RETURN_TYPES:
            if is_opaque_reference_type(annotation):
                return _resolve_opaque_type_info(annotation).class_name  # type: ignore[union-attr]
            error_fn(
                f"Return has unsupported type {annotation}. "
                f"The valid types are: {SUPPORTED_RETURN_TYPES}."
            )

        return SUPPORTED_RETURN_TYPES[annotation]

    args = typing.get_args(annotation)
    for arg in args:
        if arg not in SUPPORTED_RETURN_TYPES and not is_opaque_reference_type(arg):
            error_fn(
                f"Return has unsupported type {annotation}. "
                f"The valid types are: {SUPPORTED_RETURN_TYPES}."
            )

    def _return_type_str(arg):
        if ty := SUPPORTED_RETURN_TYPES.get(arg):
            return ty
        return _resolve_opaque_type_info(arg).class_name  # type: ignore[union-attr]

    output_ty = ", ".join(_return_type_str(arg) for arg in args)

    # use (()) to represent tuple with single element
    if len(args) == 1:
        output_ty = "(" + output_ty + ")"
    return "(" + output_ty + ")"