def sym_min(a, b):
    """SymInt-aware utility for min()."""
    if overrides.has_torch_function((a, b)):
        return overrides.handle_torch_function(sym_min, (a, b), a, b)
    if isinstance(a, (SymInt, SymFloat)):
        return a.__sym_min__(b)
    elif isinstance(b, (SymInt, SymFloat)):
        return b.__sym_min__(a)

    all_types, float_types = __all_and_float_types()

    if not isinstance(a, all_types):
        raise AssertionError(f"expected {all_types}, got {type(a)}")
    if not isinstance(b, all_types):
        raise AssertionError(f"expected {all_types}, got {type(b)}")
    if isinstance(a, float_types) or isinstance(b, float_types):
        return builtins.float(builtins.min(a, b))  # type: ignore[call-overload]
    else:
        return builtins.min(a, b)