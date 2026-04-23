def _lattice_result_type(*args):
    dtypes, weak_types = zip(*(_dtype_and_weaktype(arg) for arg in args))
    if len(dtypes) == 1:
        out_dtype = dtypes[0]
        out_weak_type = weak_types[0]
    elif len(set(dtypes)) == 1 and not all(weak_types):
        # Trivial promotion case. This allows extended dtypes through.
        out_dtype = dtypes[0]
        out_weak_type = False
    elif all(weak_types):
        # If all inputs are weakly typed, we compute the bound of the
        # strongly-typed counterparts and apply the weak type at the end. This
        # avoids returning the incorrect result with non-canonical weak types
        # (e.g. weak int16).
        out_dtype = _least_upper_bound(
            *{_respect_weak_type(d, False) for d in dtypes}
        )
        out_weak_type = True
    else:
        out_dtype = _least_upper_bound(
            *{_respect_weak_type(d, w) for d, w in zip(dtypes, weak_types)}
        )
        out_weak_type = any(out_dtype is t for t in WEAK_TYPES)

    out_weak_type = (out_dtype != "bool") and out_weak_type
    precision = config.floatx()[-2:]
    if out_weak_type:
        out_dtype = _resolve_weak_type(out_dtype, precision=precision)

    # Force to be 32-bit dtype when encountering 64-bit dtype. This is to
    # be aligned with JAX's default behavior.
    out_dtype = BIT64_TO_BIT32_DTYPE.get(out_dtype, out_dtype)
    return out_dtype