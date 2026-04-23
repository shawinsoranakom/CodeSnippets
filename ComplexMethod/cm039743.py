def isdtype(
    dtype: DType, 
    kind: DType | str | tuple[DType | str, ...],
    *,
    _tuple: bool = True, # Disallow nested tuples
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
        return _builtin_any(isdtype(dtype, k, _tuple=False) for k in kind)
    elif isinstance(kind, str):
        if kind == 'bool':
            return dtype == torch.bool
        elif kind == 'signed integer':
            return dtype in _int_dtypes and dtype.is_signed
        elif kind == 'unsigned integer':
            return dtype in _int_dtypes and not dtype.is_signed
        elif kind == 'integral':
            return dtype in _int_dtypes
        elif kind == 'real floating':
            return dtype.is_floating_point
        elif kind == 'complex floating':
            return dtype.is_complex
        elif kind == 'numeric':
            return isdtype(dtype, ('integral', 'real floating', 'complex floating'))
        else:
            raise ValueError(f"Unrecognized data type kind: {kind!r}")
    else:
        return dtype == kind