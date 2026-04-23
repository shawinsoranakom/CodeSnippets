def _determine_input_dtype(
    param: ir.schemas.Parameter,
    arg: AllowedArgType,
    type_binding: Mapping[ir.schemas.TypeConstraintParam, ir.TypeProtocol],
) -> ir.DataType:
    """Determine the dtype of the input that is a mix of Python constants and ir.Value."""
    if param.type_constraint in type_binding:
        # A known dtype is available because it was resolved
        return type_binding[param.type_constraint].dtype
    if len(param.type_constraint.allowed_types) == 1:
        # Only one type is allowed by the type constraint
        return next(iter(param.type_constraint.allowed_types)).dtype

    # No dtype information available. Infer from the Python constant or (in the Sequence case)
    # from a mix of Python constants and ir.Value
    if isinstance(arg, bool):
        return ir.DataType.BOOL
    if isinstance(arg, float):
        return ir.DataType.FLOAT
    if isinstance(arg, int):
        return ir.DataType.INT64
    if isinstance(arg, str):
        return ir.DataType.STRING
    if isinstance(arg, (ir.Tensor, ir.TensorProtocol)):
        return arg.dtype
    if isinstance(arg, complex):
        return ir.DataType.FLOAT
    if arg is None:
        return ir.DataType.UNDEFINED

    # Handle sequences
    if isinstance(arg, (tuple, list)):
        if len(arg) == 0:
            # Special case: Treat empty sequence as INT64 as they are typically used for shape
            return ir.DataType.INT64

        # Try to obtain the dtype from one of the values
        for val in arg:
            if isinstance(val, ir.Value) and val.dtype is not None:
                return val.dtype

        if any(isinstance(val, float) for val in arg):
            # If any float is present, the dtype is float
            return ir.DataType.FLOAT
        elif any(isinstance(val, int) for val in arg):
            # Otherwise if any int is present, the dtype is int
            return ir.DataType.INT64

    raise ValueError(
        f"Could not determine the dtype for the input '{param.name}'. "
        f"param={param}, arg={arg}, param_type_constraint={param.type_constraint}, "
        f"type_binding={type_binding}"
    )