def _multi_tensor_rmsprop(
    params: list[Tensor],
    grads: list[Tensor],
    square_avgs: list[Tensor],
    grad_avgs: list[Tensor],
    momentum_buffer_list: list[Tensor],
    state_steps: list[Tensor],
    *,
    lr: float,
    alpha: float,
    eps: float,
    weight_decay: float,
    momentum: float,
    centered: bool,
    maximize: bool,
    differentiable: bool,
    capturable: bool,
    has_complex: bool,
) -> None:
    if len(params) == 0:
        return

    if differentiable:
        raise AssertionError("_foreach ops don't support autograd")

    # If compiling, the compiler will handle cudagraph checks, see note [torch.compile x capturable]
    if not torch.compiler.is_compiling() and capturable:
        capturable_supported_devices = _get_capturable_supported_devices()
        if not all(
            p.device.type == step.device.type
            and p.device.type in capturable_supported_devices
            for p, step in zip(params, state_steps, strict=True)
        ):
            raise AssertionError(
                f"If capturable=True, params and state_steps must be on supported devices: {capturable_supported_devices}."
            )

    lr = _to_scalar(lr)

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, square_avgs, grad_avgs, momentum_buffer_list, state_steps]  # type: ignore[list-item]
    )
    for (
        (
            grouped_params_,
            grouped_grads_,
            grouped_square_avgs_,
            grouped_grad_avgs_,
            grouped_momentum_buffer_list_,
            grouped_state_steps_,
        )
    ), _ in grouped_tensors.values():
        grouped_params = cast(list[Tensor], grouped_params_)
        grouped_grads = cast(list[Tensor], grouped_grads_)
        grouped_square_avgs = cast(list[Tensor], grouped_square_avgs_)
        grouped_state_steps = cast(list[Tensor], grouped_state_steps_)

        if has_complex:
            state_and_grads = [grouped_grads, grouped_square_avgs]
            if momentum > 0:
                grouped_momentum_buffer_list = cast(
                    list[Tensor], grouped_momentum_buffer_list_
                )
                state_and_grads.append(grouped_momentum_buffer_list)
            if centered:
                grouped_grad_avgs = cast(list[Tensor], grouped_grad_avgs_)
                state_and_grads.append(grouped_grad_avgs)
            _view_as_real(grouped_params, *state_and_grads)

        if maximize:
            grouped_grads = torch._foreach_neg(grouped_grads)  # type: ignore[assignment]

        # Update steps
        # If steps are on CPU, foreach will fall back to the slow path, which is a for-loop calling t.add(1) over
        # and over. 1 will then be wrapped into a Tensor over and over again, which is slower than if we just
        # wrapped it once now. The alpha is required to assure we go to the right overload.
        if not torch.compiler.is_compiling() and grouped_state_steps[0].is_cpu:
            torch._foreach_add_(
                grouped_state_steps, torch.tensor(1.0, device="cpu"), alpha=1.0
            )
        else:
            torch._foreach_add_(grouped_state_steps, 1)

        if weight_decay != 0:
            # Reuse the intermediate memory (grouped_grads) already allocated for maximize
            if maximize:
                torch._foreach_add_(grouped_grads, grouped_params, alpha=weight_decay)
            else:
                grouped_grads = torch._foreach_add(  # type: ignore[assignment]
                    grouped_grads, grouped_params, alpha=weight_decay
                )

        torch._foreach_mul_(grouped_square_avgs, alpha)
        torch._foreach_addcmul_(
            grouped_square_avgs, grouped_grads, grouped_grads, value=1 - alpha
        )

        if centered:
            grouped_grad_avgs = cast(list[Tensor], grouped_grad_avgs_)
            torch._foreach_lerp_(grouped_grad_avgs, grouped_grads, 1 - alpha)
            avg = torch._foreach_addcmul(
                grouped_square_avgs, grouped_grad_avgs, grouped_grad_avgs, value=-1
            )
            torch._foreach_sqrt_(avg)
            torch._foreach_add_(avg, eps)
        else:
            avg = torch._foreach_sqrt(grouped_square_avgs)
            torch._foreach_add_(avg, eps)

        if momentum > 0:
            grouped_momentum_buffer_list = cast(
                list[Tensor], grouped_momentum_buffer_list_
            )
            torch._foreach_mul_(grouped_momentum_buffer_list, momentum)
            torch._foreach_addcdiv_(grouped_momentum_buffer_list, grouped_grads, avg)
            # If LR is a tensor, the else branch will internally call item()
            # which will cause silent incorrectness if we are capturing
            if capturable and isinstance(lr, torch.Tensor):
                momentum_lr = torch._foreach_mul(grouped_momentum_buffer_list, -lr)
                torch._foreach_add_(grouped_params, momentum_lr)
            else:
                torch._foreach_add_(
                    grouped_params, grouped_momentum_buffer_list, alpha=-lr
                )
        else:
            # If LR is a tensor, the else branch will internally call item()
            # which will cause silent incorrectness if we are capturing
            if capturable and isinstance(lr, torch.Tensor):
                torch._foreach_div_(avg, -lr)
                torch._foreach_addcdiv_(grouped_params, grouped_grads, avg)
            else:
                torch._foreach_addcdiv_(grouped_params, grouped_grads, avg, value=-lr)