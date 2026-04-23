def has_static_value(a: SymBool | SymFloat | SymInt | bool | float | int) -> bool:
    """
    User-code friendly utility to check if a value is static or dynamic.
    Returns true if given a constant, or a symbolic expression with a fixed value.

    Args:
        a (Union[SymBool, SymFloat, SymInt, bool, float, int]): Object to test
    """
    if not isinstance(a, BoolLike + FloatLike + IntLike):
        raise AssertionError(f"Expected BoolLike/FloatLike/IntLike, got {type(a)}")
    if (
        isinstance(a, BoolLike)
        and is_concrete_bool(a)  # type: ignore[arg-type]
        or isinstance(a, FloatLike)
        and is_concrete_float(a)  # type: ignore[arg-type]
        or isinstance(a, IntLike)
        and is_concrete_int(a)  # type: ignore[arg-type]
    ):
        return True

    if not isinstance(a, py_sym_types):
        raise AssertionError(f"Expected py_sym_types, got {type(a)}")
    return a.node.shape_env.bound_sympy(a.node.expr).is_singleton()