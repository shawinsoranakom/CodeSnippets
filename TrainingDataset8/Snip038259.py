def is_function(x: object) -> TypeGuard[types.FunctionType]:
    """Return True if x is a function."""
    return isinstance(x, types.FunctionType)