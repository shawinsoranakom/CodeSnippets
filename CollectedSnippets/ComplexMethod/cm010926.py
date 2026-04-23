def _multi_tensor_adadelta(
    params: list[Tensor],
    grads: list[Tensor],
    square_avgs: list[Tensor],
    acc_deltas: list[Tensor],
    state_steps: list[Tensor],
    *,
    lr: float,
    rho: float,
    eps: float,
    weight_decay: float,
    maximize: bool,
    differentiable: bool,
    capturable: bool,
    has_complex: bool,
) -> None:
    if differentiable:
        raise AssertionError("_foreach ops don't support autograd")

    # If compiling, the compiler will handle cudagraph checks, see note [torch.compile x capturable]
    if not torch.compiler.is_compiling() and capturable:
        capturable_supported_devices = _get_capturable_supported_devices(
            supports_xla=False
        )
        if not all(
            p.device.type == step.device.type
            and p.device.type in capturable_supported_devices
            for p, step in zip(params, state_steps, strict=True)
        ):
            raise AssertionError(
                f"If capturable=True, params and state_steps must be on supported devices: {capturable_supported_devices}."
            )

    if len(params) == 0:
        return

    lr = _to_scalar(lr)

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, square_avgs, acc_deltas, state_steps]  # type: ignore[list-item]
    )
    for (
        device_params_,
        device_grads_,
        device_square_avgs_,
        device_acc_deltas_,
        device_state_steps_,
    ), _ in grouped_tensors.values():
        device_params = cast(list[Tensor], device_params_)
        device_grads = cast(list[Tensor], device_grads_)
        device_square_avgs = cast(list[Tensor], device_square_avgs_)
        device_acc_deltas = cast(list[Tensor], device_acc_deltas_)
        device_state_steps = cast(list[Tensor], device_state_steps_)
        if has_complex:
            _view_as_real(
                device_params, device_grads, device_square_avgs, device_acc_deltas
            )

        # Update steps
        # If steps are on CPU, foreach will fall back to the slow path, which is a for-loop calling t.add(1) over
        # and over. 1 will then be wrapped into a Tensor over and over again, which is slower than if we just
        # wrapped it once now. The alpha is required to assure we go to the right overload.
        if not torch.compiler.is_compiling() and device_state_steps[0].is_cpu:
            torch._foreach_add_(
                device_state_steps, torch.tensor(1.0, device="cpu"), alpha=1.0
            )
        else:
            torch._foreach_add_(device_state_steps, 1)

        if maximize:
            device_grads = torch._foreach_neg(device_grads)  # type: ignore[assignment]

        if weight_decay != 0:
            # Reuse the intermediate memory (device_grads) already allocated for maximize
            if maximize:
                torch._foreach_add_(device_grads, device_params, alpha=weight_decay)
            else:
                device_grads = torch._foreach_add(  # type: ignore[assignment]
                    device_grads, device_params, alpha=weight_decay
                )

        torch._foreach_mul_(device_square_avgs, rho)
        torch._foreach_addcmul_(
            device_square_avgs, device_grads, device_grads, value=1 - rho
        )

        std = torch._foreach_add(device_square_avgs, eps)
        torch._foreach_sqrt_(std)

        deltas = torch._foreach_add(device_acc_deltas, eps)
        torch._foreach_sqrt_(deltas)
        torch._foreach_div_(deltas, std)
        torch._foreach_mul_(deltas, device_grads)

        torch._foreach_mul_(device_acc_deltas, rho)
        torch._foreach_addcmul_(device_acc_deltas, deltas, deltas, value=1 - rho)

        # If LR is a tensor, the else branch will internally call item()
        # which will cause silent incorrectness if we are capturing
        if capturable and isinstance(lr, torch.Tensor):
            torch._foreach_mul_(deltas, -lr)
            torch._foreach_add_(device_params, deltas)
        else:
            torch._foreach_add_(device_params, deltas, alpha=-lr)