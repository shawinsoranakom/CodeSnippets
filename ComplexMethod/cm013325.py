def _filter_unary_elementwise_tensor(a, *, op):
    # short-circuits for boolean tensors
    if a.dtype is torch.bool:
        return a

    low, high = op.domain
    is_floating = a.dtype.is_floating_point or a.dtype.is_complex
    low = low if low is None or not is_floating else low + op._domain_eps
    high = high if high is None or not is_floating else high - op._domain_eps

    if a.dtype is torch.uint8 and low is not None:
        low = max(low, 0)

    if not a.dtype.is_floating_point and not a.dtype.is_complex:
        low = math.ceil(low) if low is not None else None
        high = math.floor(high) if high is not None else None

    if op.reference_numerics_filter is not None:
        condition, safe_value = op.reference_numerics_filter
        _replace_values_in_tensor(a, condition, safe_value)

    if low is not None or high is not None:
        if a.dtype.is_complex:
            a.real.clamp_(low, high)
            a.imag.clamp_(low, high)
        else:
            a.clamp_(min=low, max=high)

    return a