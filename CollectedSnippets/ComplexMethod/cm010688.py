def _fused_rms_norm_backward(
    grad_out: Tensor,
    input: Tensor,
    normalized_shape: list[int],
    rstd: Tensor,
    weight: Tensor | None,
    output_mask: list[bool],
) -> tuple[Tensor | None, Tensor | None]:
    input_shape = input.shape
    input_ndim = input.dim()
    computation_dtype = utils.get_computation_dtype(input.dtype)

    grad_out_cast = grad_out.to(
        computation_dtype, memory_format=torch.contiguous_format
    )
    input_cast = input.to(computation_dtype, memory_format=torch.contiguous_format)
    weight_cast = (
        weight.to(computation_dtype, memory_format=torch.contiguous_format)
        if weight is not None
        else None
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
    from torch.fx.experimental.symbolic_shapes import guard_or_false

    if guard_or_false(M == 0) or guard_or_false(N == 0):
        return (
            input.new_zeros(input_shape) if output_mask[0] else None,
            input.new_zeros(input_shape[axis:]) if output_mask[1] else None,
        )

    rstd = _unsqueeze_to_dim(rstd, input_cast.dim())  # type: ignore[union-attr]
    if weight_cast is not None:
        grad_x_hat = grad_out_cast * weight_cast
    else:
        grad_x_hat = grad_out_cast

    d_input: Tensor | None = None
    d_weight: Tensor | None = None

    x_hat = input_cast * rstd

    if output_mask[0]:
        sum_val = torch.sum(x_hat * grad_x_hat, dim=inner_dim_indices, keepdim=True)
        d_input = (grad_x_hat - (x_hat / N) * sum_val) * rstd

    if output_mask[1] and weight_cast is not None:
        d_weight_full_shape = grad_out_cast * x_hat
        if len(outer_dim_indices) > 0:
            d_weight = torch.sum(
                d_weight_full_shape, dim=outer_dim_indices, keepdim=False
            )
        else:
            d_weight = d_weight_full_shape

    return (
        _maybe_cast(d_input, input.dtype),
        _maybe_cast(d_weight, input.dtype),
    )