def div_mode(a, b, rounding_mode=None):
    both_integer = is_integer_type(a) and is_integer_type(b)
    both_boolean = is_boolean_type(a) and is_boolean_type(b)

    # floordiv and truncdiv need special handling for integer tensors on Triton,
    # see the discussion at https://github.com/triton-lang/triton/issues/605
    if rounding_mode == "floor":
        assert not both_boolean, "floordiv operands can not be boolean at the same time"
        # Use div_rn (IEEE round-to-nearest) instead of truediv here because
        # Triton's default division uses an approximate reciprocal, which can
        # produce a result slightly below the true quotient and cause floor()
        # to round down by one.
        return floordiv(a, b) if both_integer else floor(_div_rn(a, b))
    if rounding_mode == "trunc":
        assert not both_boolean, "truncdiv operands can not be boolean at the same time"
        return truncdiv(a, b) if both_integer else trunc(div(a, b))
    return div(a, b)