def isclose(
    a: Array | complex,
    b: Array | complex,
    *,
    rtol: float = 1e-05,
    atol: float = 1e-08,
    equal_nan: bool = False,
    xp: ModuleType,
) -> Array:  # numpydoc ignore=PR01,RT01
    """See docstring in array_api_extra._delegation."""
    a, b = asarrays(a, b, xp=xp)

    a_inexact = xp.isdtype(a.dtype, ("real floating", "complex floating"))
    b_inexact = xp.isdtype(b.dtype, ("real floating", "complex floating"))
    if a_inexact or b_inexact:
        # prevent warnings on NumPy and Dask on inf - inf
        mxp = meta_namespace(a, b, xp=xp)
        out = apply_where(
            xp.isinf(a) | xp.isinf(b),
            (a, b),
            lambda a, b: mxp.isinf(a) & mxp.isinf(b) & (mxp.sign(a) == mxp.sign(b)),  # pyright: ignore[reportUnknownArgumentType]
            # Note: inf <= inf is True!
            lambda a, b: mxp.abs(a - b) <= (atol + rtol * mxp.abs(b)),  # pyright: ignore[reportUnknownArgumentType]
            xp=xp,
        )
        if equal_nan:
            out = xp.where(xp.isnan(a) & xp.isnan(b), True, out)
        return out

    if xp.isdtype(a.dtype, "bool") or xp.isdtype(b.dtype, "bool"):
        if atol >= 1 or rtol >= 1:
            return xp.ones_like(a == b)
        return a == b

    # integer types
    atol = int(atol)
    if rtol == 0:
        return xp.abs(a - b) <= atol

    # Don't rely on OverflowError, as it is not guaranteed by the Array API.
    nrtol = int(1.0 / rtol)
    if nrtol > xp.iinfo(b.dtype).max:
        # rtol * max_int < 1, so it's inconsequential
        return xp.abs(a - b) <= atol
    return xp.abs(a - b) <= (atol + xp.abs(b) // nrtol)