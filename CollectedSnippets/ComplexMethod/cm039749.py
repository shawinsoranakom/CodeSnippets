def isdtype(
    dtype: DType,
    kind: DType | str | tuple[DType | str, ...],
    xp: Namespace,
    *,
    _tuple: bool = True,  # Disallow nested tuples
) -> bool:
    """
    Returns a boolean indicating whether a provided dtype is of a specified data type ``kind``.

    Note that outside of this function, this compat library does not yet fully
    support complex numbers.

    See
    https://data-apis.org/array-api/latest/API_specification/generated/array_api.isdtype.html
    for more details
    """
    if isinstance(kind, tuple) and _tuple:
        return any(
            isdtype(dtype, k, xp, _tuple=False)
            for k in cast("tuple[DType | str, ...]", kind)
        )
    elif isinstance(kind, str):
        if kind == "bool":
            return dtype == xp.bool_
        elif kind == "signed integer":
            return xp.issubdtype(dtype, xp.signedinteger)
        elif kind == "unsigned integer":
            return xp.issubdtype(dtype, xp.unsignedinteger)
        elif kind == "integral":
            return xp.issubdtype(dtype, xp.integer)
        elif kind == "real floating":
            return xp.issubdtype(dtype, xp.floating)
        elif kind == "complex floating":
            return xp.issubdtype(dtype, xp.complexfloating)
        elif kind == "numeric":
            return xp.issubdtype(dtype, xp.number)
        else:
            raise ValueError(f"Unrecognized data type kind: {kind!r}")
    else:
        # This will allow things that aren't required by the spec, like
        # isdtype(np.float64, float) or isdtype(np.int64, 'l'). Should we be
        # more strict here to match the type annotation? Note that the
        # array_api_strict implementation will be very strict.
        return dtype == kind