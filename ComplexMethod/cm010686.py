def native_layer_norm_backward(
    grad_out: Tensor,
    input: Tensor,
    normalized_shape: list[int],
    mean: Tensor,
    rstd: Tensor,
    weight: Tensor | None,
    bias: Tensor | None,
    output_mask: list[bool],
) -> tuple[Tensor | None, Tensor | None, Tensor | None]:
    input_shape = input.shape
    input_ndim = input.dim()
    computation_dtype = utils.get_computation_dtype(input.dtype)
    grad_out_cast, input_cast, weight_cast, bias_cast = (
        x.to(computation_dtype, memory_format=torch.contiguous_format)
        if x is not None
        else x
        for x in (grad_out, input, weight, bias)
    )
    if grad_out_cast is None:
        raise AssertionError("grad_out_cast should not be None")

    axis = input_ndim - len(normalized_shape)
    inner_dims = input_shape[axis:]
    outer_dims = input_shape[:axis]
    inner_dim_indices: list[int] = []
    outer_dim_indices: list[int] = []
    for i in range(input_ndim):
        if i >= axis:
            inner_dim_indices.append(i)
        else:
            outer_dim_indices.append(i)

    N = prod(inner_dims)  # type: ignore[arg-type]
    M = prod(outer_dims)  # type: ignore[arg-type]
    from torch.fx.experimental.symbolic_shapes import statically_known_true

    if statically_known_true(M == 0) or statically_known_true(N == 0):
        return (
            input.new_zeros(input_shape) if output_mask[0] else None,
            input.new_zeros(input_shape[axis:]) if output_mask[1] else None,
            input.new_zeros(input_shape[axis:]) if output_mask[2] else None,
        )
    mean = _unsqueeze_to_dim(mean, input_cast.dim())  # type: ignore[union-attr]
    rstd = _unsqueeze_to_dim(rstd, input_cast.dim())  # type: ignore[union-attr]
    if input_cast is None:
        raise AssertionError("input_cast should not be None")
    x_hat = (input_cast - mean) * rstd
    if weight_cast is not None:
        grad_x_hat = grad_out_cast * weight_cast
    else:
        grad_x_hat = grad_out_cast
    a = grad_x_hat * N
    b = torch.sum(grad_x_hat, inner_dim_indices, True)
    c1 = torch.mul(grad_x_hat, x_hat)
    c2 = torch.sum(c1, inner_dim_indices, True)
    c3 = torch.mul(x_hat, c2)

    inner = a - b - c3
    d_input: Tensor | None = None
    d_weight: Tensor | None = None
    d_bias: Tensor | None = None
    if output_mask[0]:
        d_input = (rstd / N) * inner

    if output_mask[1] and weight_cast is not None:
        if len(outer_dim_indices) > 0:
            d_weight = torch.sum(grad_out_cast * x_hat, outer_dim_indices, False)
        else:
            d_weight = grad_out_cast * x_hat

    if output_mask[2] and bias_cast is not None:
        if len(outer_dim_indices) > 0:
            d_bias = torch.sum(grad_out_cast, outer_dim_indices, False)
        else:
            d_bias = grad_out_cast.clone()

    return (
        _maybe_cast(d_input, input.dtype),
        _maybe_cast(d_weight, weight.dtype if weight is not None else None),
        _maybe_cast(d_bias, bias.dtype if bias is not None else None),
    )