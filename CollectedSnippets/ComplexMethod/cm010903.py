def _fused_sgd(
    params: list[Tensor],
    grads: list[Tensor],
    momentum_buffer_list: list[Tensor | None],
    grad_scale: Tensor | None,
    found_inf: Tensor | None,
    *,
    weight_decay: float,
    momentum: float,
    lr: float,
    dampening: float,
    nesterov: bool,
    maximize: bool,
    has_sparse_grad: bool,
) -> None:
    if not params:
        return
    if has_sparse_grad:
        raise RuntimeError("`_fused_sgd` does not support sparse gradients")
    grad_scale_dict: DeviceDict = (
        {grad_scale.device: grad_scale} if grad_scale is not None else {}
    )
    found_inf_dict: DeviceDict = (
        {found_inf.device: found_inf} if found_inf is not None else {}
    )

    no_momentum_buffer = momentum == 0
    is_first_step = (
        all(t is None for t in momentum_buffer_list) and not no_momentum_buffer
    )
    if is_first_step:
        for i, g in enumerate(grads):
            momentum_buffer_list[i] = torch.empty_like(g)
    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, momentum_buffer_list],  # type: ignore[list-item]
        with_indices=False,
    )
    for (device, _), (
        (device_params_, device_grads_, device_momentum_buffer_list),
        _,
    ) in grouped_tensors.items():
        device_params: list[Tensor] = cast(list[Tensor], device_params_)
        device_grads: list[Tensor] = cast(list[Tensor], device_grads_)
        device_grad_scale, device_found_inf = None, None
        if grad_scale is not None:
            device_grad_scale = grad_scale_dict.setdefault(
                device, grad_scale.to(device)
            )
        if found_inf_dict is not None and found_inf is not None:
            device_found_inf = found_inf_dict.setdefault(device, found_inf.to(device))
        torch._fused_sgd_(
            device_params,
            device_grads,
            []
            if no_momentum_buffer
            else cast(list[Tensor], device_momentum_buffer_list),
            weight_decay=weight_decay,
            momentum=momentum,
            lr=lr,
            dampening=dampening,
            nesterov=nesterov,
            maximize=maximize,
            is_first_step=is_first_step,
            grad_scale=device_grad_scale,
            found_inf=device_found_inf,
        )