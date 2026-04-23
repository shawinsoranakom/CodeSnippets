def clip_grad_norm_(
    parameters: Iterable[torch.Tensor],
    max_norm: float,
    norm_type: float = 2.0,
    error_if_nonfinite: bool = False,
    foreach: bool | None = None,
) -> torch.Tensor:
    """
    Clip the gradient norm of an iterable of parameters.
    """
    # Filter out parameters with no gradients
    parameters = [p for p in parameters if p.grad is not None]
    assert len(parameters) > 0, "No parameters with gradients found"

    # Calculate total norm
    if norm_type == float("inf"):
        total_norm = max(p.grad.detach().abs().max() for p in parameters)
    else:
        total_norm = torch.norm(torch.stack([torch.norm(p.grad.detach(), norm_type) for p in parameters]), norm_type)

    # Convert DTensor to local tensor if needed
    if isinstance(total_norm, DTensor):
        total_norm = total_norm.full_tensor()

    # Clip gradients
    clip_coef = max_norm / (total_norm + 1e-6)
    if clip_coef < 1:
        for p in parameters:
            p.grad.detach().mul_(clip_coef)

    return total_norm
