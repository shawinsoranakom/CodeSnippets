def sym_max(a, b):
    """
    SymInt-aware utility for max which avoids branching on a < b.
    Unlike builtins.max(), this only works for int/float, and it always
    promotes to float if any argument is float (unlike builtins.max, which
    will faithfully preserve the type of the input argument).
    """
    if overrides.has_torch_function((a, b)):
        return overrides.handle_torch_function(sym_max, (a, b), a, b)
    if isinstance(a, (SymInt, SymFloat)):
        return a.__sym_max__(b)
    elif isinstance(b, (SymInt, SymFloat)):
        # Due to promotion semantics, this is operator is commutative:
        # max(1, 1.0) === max(1.0, 1) === 1.0
        return b.__sym_max__(a)
    # TODO: Probably can make bool work too, just lazy

    all_types, float_types = __all_and_float_types()

    if not isinstance(a, all_types):
        raise AssertionError(f"expected {all_types}, got {type(a)}")
    if not isinstance(b, all_types):
        raise AssertionError(f"expected {all_types}, got {type(b)}")
    if isinstance(a, float_types) or isinstance(b, float_types):
        return builtins.float(builtins.max(a, b))  # type: ignore[call-overload]
    else:
        return builtins.max(a, b)