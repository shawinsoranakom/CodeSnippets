def hardtanh(
    a: TensorLikeType,
    min_val: NumberType = -1,
    max_val: NumberType = 1,
    inplace: bool = False,
) -> TensorLikeType:
    """
    Reference implementation of torch.nn.functional.hardtanh
    """
    if inplace:
        raise NotImplementedError
    if utils.is_boolean_dtype(a.dtype):
        raise RuntimeError("Bool inputs not supported for hardtanh")

    # preserve legacy behavior of boundaries not causing type promotion
    if utils.is_integer_dtype(a.dtype):
        min_val = int(min_val)  # type: ignore[arg-type]
        max_val = int(max_val)  # type: ignore[arg-type]
        if not (a.dtype != torch.uint8 or (min_val >= 0 and max_val >= 0)):
            raise RuntimeError(
                "Cannot do hardtanh on an unsigned type with negative limits"
            )

    if min_val > max_val:  # type: ignore[operator]
        raise ValueError("min_val cannot be greater than max_val")

    return torch.clamp(a, min_val, max_val)