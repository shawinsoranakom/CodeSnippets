def _nll_loss_backward(
    grad_output: Tensor,
    self: Tensor,
    target: Tensor,
    weight: Tensor | None,
    reduction: int,
    ignore_index: int,
    total_weight: Tensor,
) -> Tensor:
    channel_dim = 0 if self.dim() < 2 else 1
    if reduction == Reduction.MEAN.value:
        grad_output = grad_output / total_weight

    # When self is 1D (no batch dim), the C++ kernel only uses target[0].
    # Reduce target to a scalar so the subsequent unsqueeze produces a 1D
    # tensor matching self's dimensionality.
    if self.dim() == 1 and target.dim() > 0:
        target = target[0]

    target = target.unsqueeze(channel_dim)
    safe_target = torch.where(target != ignore_index, target, 0)
    grad_input = torch.zeros_like(self)
    grad_input = torch.scatter(grad_input, channel_dim, safe_target, -1.0)

    if grad_input.dim() > grad_output.dim() > 0:
        grad_output = grad_output.unsqueeze(channel_dim)

    if weight is not None:
        new_shape = [1 for _ in range(self.dim())]
        new_shape[channel_dim] = weight.shape[0]
        weight = weight.reshape(new_shape)
        grad_output = grad_output * weight

    grad_output = torch.where(target != ignore_index, grad_output, 0)

    return grad_input * grad_output