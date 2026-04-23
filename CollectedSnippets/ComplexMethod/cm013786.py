def clip_grad_value_(
    parameters: _tensor_or_tensors,
    clip_value: float,
    foreach: bool | None = None,
) -> None:
    r"""Clip the gradients of an iterable of parameters at specified value.

    Gradients are modified in-place.

    Args:
        parameters (Iterable[Tensor] or Tensor): an iterable of Tensors or a
            single Tensor that will have gradients normalized
        clip_value (float): maximum allowed value of the gradients.
            The gradients are clipped in the range
            :math:`\left[\text{-clip\_value}, \text{clip\_value}\right]`
        foreach (bool, optional): use the faster foreach-based implementation
            If ``None``, use the foreach implementation for CUDA and CPU native tensors and
            silently fall back to the slow implementation for other device types.
            Default: ``None``
    """
    if isinstance(parameters, torch.Tensor):
        parameters = [parameters]
    clip_value = float(clip_value)

    grads = [p.grad for p in parameters if p.grad is not None]
    # pyrefly: ignore [bad-argument-type]
    grouped_grads = _group_tensors_by_device_and_dtype([grads])

    for (device, _), ([grads], _) in grouped_grads.items():
        if (
            foreach is None
            and _has_foreach_support(cast(list[Tensor], grads), device=device)
        ) or (foreach and _device_has_foreach_support(device)):
            torch._foreach_clamp_min_(cast(list[Tensor], grads), -clip_value)
            torch._foreach_clamp_max_(cast(list[Tensor], grads), clip_value)
        elif foreach:
            raise RuntimeError(
                f"foreach=True was passed, but can't use the foreach API on {device.type} tensors"
            )
        else:
            for grad in grads:
                cast(Tensor, grad).clamp_(min=-clip_value, max=clip_value)