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

    axis = input_ndim - len(normalized_shape)
    inner_dims = input_shape[axis:]
    outer_dims = input_shape[:axis]
    inner_dim_indices = list(range(axis, input_ndim))
    outer_dim_indices = list(range(axis))

    N = 1
    for i in inner_dims:
        N *= i
    M = 1
    for i in outer_dims:
        M *= i
    if M <= 0 or N <= 0:
        return (
            input.new_zeros(input_shape),
            input.new_zeros(input_shape[axis:]),
            input.new_zeros(input_shape[axis:]),
        )

    mean_, rstd_ = recompute_mean_var(input, rstd, inner_dim_indices, keepdim=True)

    x_hat = (input - mean_) * rstd_
    if weight is not None:
        grad_x_hat = grad_out * weight
    else:
        grad_x_hat = grad_out
    a = grad_x_hat * N
    b = torch.sum(grad_x_hat, inner_dim_indices, True)
    c1 = torch.mul(grad_x_hat, x_hat)
    c2 = torch.sum(c1, inner_dim_indices, True)
    c3 = torch.mul(x_hat, c2)
    inner = a - b - c3

    if output_mask[0]:
        d_input: Tensor | None = (rstd_ / N) * inner
    else:
        d_input = torch.zeros_like(input)  # should be None but doesn't work with vjp

    if output_mask[1] and weight is not None:
        if len(outer_dim_indices) > 0:
            d_weight: Tensor | None = torch.sum(
                grad_out * x_hat, outer_dim_indices, False
            )
        else:
            d_weight = grad_out * x_hat
    elif weight is not None:
        d_weight = torch.zeros_like(weight)  # should be None but doesn't work with vjp
    else:
        d_weight = torch.zeros(())  # should be None but doesn't work with vjp

    if output_mask[2] and bias is not None:
        if len(outer_dim_indices) > 0:
            d_bias: Tensor | None = torch.sum(grad_out, outer_dim_indices, False)
        else:
            d_bias = grad_out.clone()
    elif bias is not None:
        d_bias = torch.zeros_like(bias)  # should be None but doesn't work with vjp
    else:
        d_bias = torch.zeros(())  # should be None but doesn't work with vjp

    return (d_input, d_weight, d_bias)