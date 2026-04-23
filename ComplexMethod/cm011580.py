def pow(
    a: TensorLikeType | NumberType,
    b: TensorLikeType | NumberType,
) -> TensorLikeType:
    if not (isinstance(a, TensorLikeType) or isinstance(b, TensorLikeType)):
        raise AssertionError("at least one of a or b must be TensorLikeType")

    if isinstance(b, Number):
        if b == 1.0:
            return a.clone()  # type: ignore[return-value,union-attr]
        elif b == 2.0:
            return a * a  # type: ignore[return-value]
        elif b == 0.5:
            return torch.sqrt(a)  # type: ignore[arg-type]
    elif isinstance(a, Number):
        if a == 1.0:
            return torch.fill(b, True)
        if a == 2.0 and (
            utils.is_float_dtype(b.dtype) or utils.is_complex_dtype(b.dtype)
        ):
            return torch.exp2(b)

    return prims.pow(a, b)