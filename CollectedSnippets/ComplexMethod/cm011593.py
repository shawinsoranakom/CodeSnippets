def native_layer_norm(
    input: Tensor,
    normalized_shape: ShapeType,
    weight: Tensor | None,
    bias: Tensor | None,
    eps: float,
) -> tuple[Tensor, Tensor, Tensor]:
    from torch.fx.experimental.symbolic_shapes import sym_eq

    normalized_ndim = len(normalized_shape)
    torch._check(
        normalized_ndim >= 1,
        lambda: "Expected normalized_shape to be at least 1-dimensional, i.e., "
        + "containing at least one element, but got normalized_shape = "
        + str(normalized_shape),
    )
    # torch.Size([1, 2, 3]) == [1, 2, 3] evaluates to False
    # while torch.Size([1, 2, 3]) == (1, 2, 3) is True
    # therefore we use tuple(normalized_shape)
    torch._check(
        # pyrefly: ignore [bad-argument-type]
        weight is None or sym_eq(weight.shape, tuple(normalized_shape)),
        lambda: "Expected weight to be of same shape as normalized_shape, but got "
        + "weight of shape "
        + str(weight.shape)  # type: ignore[union-attr]
        + " and normalized_shape = "
        + str(normalized_shape),
    )
    torch._check(
        # pyrefly: ignore [bad-argument-type]
        bias is None or sym_eq(bias.shape, tuple(normalized_shape)),
        lambda: "Expected bias to be of same shape as normalized_shape, but got "
        + "bias of shape "
        + str(bias.shape)  # type: ignore[union-attr]
        + " and normalized_shape = "
        + str(normalized_shape),
    )
    torch._check(
        input.ndim >= normalized_ndim
        and sym_eq(
            input.shape[(input.ndim - normalized_ndim) :],
            tuple(normalized_shape),
        ),
        lambda: "Given normalized_shape="
        + str(normalized_shape)
        + ", expected input with shape "
        + str(normalized_shape)
        + ", but got input of size "
        + str(input.shape),
    )
    torch._check(
        not input.is_complex(),
        lambda: "native_layer_norm does not support complex inputs",
    )

    input = contiguous(input)
    if weight is not None:
        weight = contiguous(weight)
    if bias is not None:
        bias = contiguous(bias)

    axis = input.ndim - normalized_ndim
    reduction_dims = list(range(axis, input.ndim))
    out, mean, rstd = _normalize(input, reduction_dims, eps)

    if weight is None and bias is not None:
        out = out + bias
    elif weight is not None and bias is None:
        out = out * weight
    elif weight is not None and bias is not None:
        out = out * weight + bias

    out = _maybe_convert_to_dtype(out, input.dtype)  # type: ignore[assignment]
    if input.device.type in ["cpu", "mtia"]:
        mean = _maybe_convert_to_dtype(mean, input.dtype)  # type: ignore[assignment]
        rstd = _maybe_convert_to_dtype(rstd, input.dtype)  # type: ignore[assignment]
    return (out, mean, rstd)