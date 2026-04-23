def _nll_loss_and_log_softmax_backward(
    grad_output: Tensor,
    x: Tensor,
    target: Tensor,
    weight: Tensor | None,
    reduction: int,
    ignore_index: int,
    total_weight: Tensor,
    input_shape: torch.Size,
    channel_dim: int,
    mesh: DeviceMesh,
    mesh_dim: int,
) -> Tensor:
    channel_dim = 0 if x.dim() < 2 else 1
    if reduction == Reduction.MEAN.value:
        grad_output = grad_output / total_weight

    target = target.unsqueeze(channel_dim)
    safe_target = torch.where(target != ignore_index, target, 0)
    grad_input = torch.zeros_like(x)

    # The following code block is a distributed version of
    # grad_input = torch.scatter(grad_input, channel_dim, safe_target, -1.0)
    partial_placement = _MaskPartial(offset_shape=input_shape, offset_dim=channel_dim)
    safe_target = safe_target.squeeze(channel_dim).flatten()
    masked_safe_target = partial_placement._partition_value(safe_target, mesh, mesh_dim)
    # only update grad_input to -1 if not masked
    if partial_placement.mask_buffer.data is None:
        raise AssertionError
    grad_update = partial_placement.mask_buffer.data.to(grad_input.dtype) - 1.0
    arange_1d = torch.arange(
        masked_safe_target.shape[0], device=masked_safe_target.device
    )
    # The first two cases with x.dim() <= 2 are for aten.nll_loss_backward.default;
    # the last case is for aten.nll_loss2d_backward.default.
    if x.dim() == 1:
        grad_input[masked_safe_target] = grad_update
    elif x.dim() == 2:
        grad_input[arange_1d, masked_safe_target] = grad_update
    else:
        grad_input_t = grad_input.transpose(channel_dim, -1)
        intermidate_shape = grad_input_t.shape
        grad_input_2d = grad_input_t.reshape(-1, x.shape[channel_dim])
        grad_input_2d[arange_1d, masked_safe_target] = grad_update
        grad_input = grad_input_2d.view(intermidate_shape).transpose(channel_dim, -1)

    if grad_input.dim() > grad_output.dim() > 0:
        grad_output = grad_output.unsqueeze(channel_dim)

    if weight is not None:
        new_shape = [1 for _ in range(x.dim())]
        new_shape[channel_dim] = weight.shape[0]
        weight = weight.reshape(new_shape)
        # In order for fused computation to work, the following line is rewritten.
        # grad_output = grad_output * weight
        new_shape = list(x.shape)
        new_shape[channel_dim] = -1
        w = weight.expand(new_shape)
        w_target = torch.gather(w, channel_dim, target)
        grad_output = grad_output * w_target

    grad_output = torch.where(target != ignore_index, grad_output, 0)

    # NOTE: Instead of directly returning the grad_input as grad_output for log_softmax,
    # here we perform backward computation for log_softmax altogether to avoid the
    # otherwise extra all_gather communication.
    # return grad_input * grad_output
    return (grad_input + torch.exp(x)) * grad_output