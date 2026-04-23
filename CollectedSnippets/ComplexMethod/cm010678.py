def native_batch_norm_backward(
    grad_out: Tensor,
    input: Tensor,
    weight: Tensor | None,
    running_mean: Tensor | None,
    running_var: Tensor | None,
    save_mean: Tensor | None,
    save_invstd: Tensor | None,
    train: bool,
    eps: float,
    output_mask: list[bool],
) -> tuple[Tensor, Tensor | None, Tensor | None]:
    input_shape = input.shape
    input_rank = input.dim()
    if input_rank < 2:
        raise AssertionError(f"rank of the input must be at least 2, got {input_rank}")

    axis = 1
    num_features = prod(input_shape) / input_shape[axis]  # type: ignore[arg-type]
    mean = save_mean
    invstd = save_invstd
    if train:
        if save_mean is None or save_invstd is None:
            raise AssertionError(
                "when train=True, save_mean and save_invstd are required"
            )

        reduciton_dims = [0] + list(range(2, input.dim()))
        if invstd is None:
            raise AssertionError("invstd must not be None for typing")
        mean, invstd = recompute_mean_var(input, invstd, reduciton_dims, keepdim=False)
    else:
        if running_mean is None or running_var is None:
            raise AssertionError(
                "running_mean and running_var must not be None when train=False"
            )
        mean = running_mean
        invstd = torch.rsqrt(running_var + eps)

    if invstd is None or mean is None:
        raise AssertionError(
            f"invstd and mean must not be None, got invstd={invstd}, mean={mean}"
        )

    broadcast_mask = [1] * input_rank
    broadcast_mask[axis] = input_shape[axis]

    reduction_axes: list[int] = []
    for i in range(input_rank):
        if i != axis:
            reduction_axes.append(i)

    mean = torch.reshape(mean, broadcast_mask)
    norm = 1.0 / num_features
    grad_output_sum = torch.sum(grad_out, reduction_axes)
    dot_p = torch.sum(grad_out * (input - mean), reduction_axes)

    grad_mean = torch.reshape(grad_output_sum * norm, broadcast_mask)
    proj_scale = torch.reshape(torch.mul(dot_p * norm, invstd * invstd), broadcast_mask)

    if weight is None:
        grad_scale = torch.reshape(invstd, broadcast_mask) * 1.0
    else:
        grad_scale = torch.reshape(invstd * weight, broadcast_mask)

    if train:
        proj = (input - mean) * proj_scale
        grad_input = ((grad_out - proj) - grad_mean) * grad_scale
    else:
        grad_input = grad_out * grad_scale

    if output_mask[1]:
        grad_weight = dot_p * invstd
    elif weight is not None:
        grad_weight = torch.zeros_like(
            weight
        )  # should be None but doesn't work with vjp
    else:
        grad_weight = torch.zeros(())  # should be None but doesn't work with vjp

    if output_mask[2]:
        grad_bias = grad_output_sum
    else:
        grad_bias = torch.zeros_like(
            grad_output_sum
        )  # should be None but doesn't work with vjp

    return (grad_input, grad_weight, grad_bias)