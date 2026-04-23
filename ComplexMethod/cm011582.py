def isclose(
    a: TensorLikeType,
    b: TensorLikeType,
    rtol: float = 1e-05,
    atol: float = 1e-08,
    equal_nan: bool = False,
) -> TensorLikeType:
    _check_close_args(name="torch.isclose", a=a, b=b, rtol=rtol, atol=atol)

    close = eq(a, b)
    if equal_nan and (utils.is_float_dtype(a.dtype) or utils.is_complex_dtype(a.dtype)):
        close = logical_or(close, logical_and(isnan(a), isnan(b)))

    # Note: In case of zero tolerances the closeness inequality degenerates to an equality check.
    # In this case, the short-circuit prevents false positives as detailed in the paragraph below.
    if atol == 0 and rtol == 0:
        return close

    # Note [closeness error computation]
    # atol and rtol are provided as doubles, so the computation
    # rtol * other will produce a float or complex tensor.
    # When the difference (self - other) is compared to it then the
    # tensor representing the difference will also be cast to float or complex.
    # However, since (self - other) in uint8 is very likely to produce a
    # negative value, this moves the cast forward so the difference is
    # always computed in a float or complex type.
    # If the values of the integer tensors cannot be exactly represented
    # by the default scalar type then this may cause an incorrect result.
    if not utils.is_float_dtype(a.dtype) and not utils.is_complex_dtype(a.dtype):
        a = prims.convert_element_type(a, torch.get_default_dtype())
        b = prims.convert_element_type(b, torch.get_default_dtype())

    allowed_error = add(atol, abs(mul(b, rtol)))
    actual_error = abs(sub(a, b))

    # Computes finite closeness
    result = logical_or(
        close, logical_and(isfinite(actual_error), le(actual_error, allowed_error))
    )

    return result