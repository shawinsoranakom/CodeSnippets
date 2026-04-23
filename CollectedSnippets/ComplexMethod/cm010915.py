def _fused_adagrad(
    params: list[Tensor],
    grads: list[Tensor],
    state_sums: list[Tensor],
    state_steps: list[Tensor],
    grad_scale: Tensor | None,
    found_inf: Tensor | None,
    *,
    lr: float | Tensor,
    weight_decay: float,
    lr_decay: float,
    eps: float,
    has_sparse_grad: bool,
    maximize: bool,
    differentiable: bool,
    has_complex: bool,
) -> None:
    if not params:
        return
    if has_sparse_grad or has_complex:
        raise RuntimeError("`fused` does not support sparse grad or complex param")

    if differentiable:
        raise RuntimeError(
            "adagrad with fused=True does not support differentiable=True"
        )

    grad_scale_dict: DeviceDict = (
        {grad_scale.device: grad_scale} if grad_scale is not None else {}
    )
    found_inf_dict: DeviceDict = (
        {found_inf.device: found_inf} if found_inf is not None else {}
    )
    lr_dict: DeviceDict | None = (
        {lr.device: lr} if isinstance(lr, Tensor) and str(lr.device) != "cpu" else None
    )

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, state_sums, state_steps]  # type: ignore[list-item]
    )
    for (device, _), (
        (
            device_params_,
            device_grads_,
            device_state_sums_,
            device_state_steps_,
        ),
        _,
    ) in grouped_tensors.items():
        device_params = cast(list[Tensor], device_params_)
        device_grads = cast(list[Tensor], device_grads_)
        device_state_sums = cast(list[Tensor], device_state_sums_)
        device_state_steps = cast(list[Tensor], device_state_steps_)

        device_grad_scale, device_found_inf = None, None
        if grad_scale is not None:
            device_grad_scale = grad_scale_dict.setdefault(
                device, grad_scale.to(device, non_blocking=True)
            )
        if found_inf is not None:
            device_found_inf = found_inf_dict.setdefault(
                device, found_inf.to(device, non_blocking=True)
            )
        if lr_dict is not None and device not in lr_dict:
            lr_dict[device] = lr.to(device=device, non_blocking=True)  # type: ignore[union-attr]
            lr = lr_dict[device]
        torch._foreach_add_(device_state_steps, 1)
        torch._fused_adagrad_(
            device_params,
            device_grads,
            device_state_sums,
            device_state_steps,
            lr=lr,
            lr_decay=lr_decay,
            weight_decay=weight_decay,
            eps=eps,
            maximize=maximize,
            grad_scale=device_grad_scale,
            found_inf=device_found_inf,
        )
        if device_found_inf is not None:
            torch._foreach_sub_(
                device_state_steps, [device_found_inf] * len(device_state_steps)
            )