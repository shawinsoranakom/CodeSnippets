def _multi_tensor_adamax(
    params: list[Tensor],
    grads: list[Tensor],
    exp_avgs: list[Tensor],
    exp_infs: list[Tensor],
    state_steps: list[Tensor],
    *,
    eps: float,
    beta1: float,
    beta2: float,
    lr: float,
    weight_decay: float,
    maximize: bool,
    differentiable: bool,
    capturable: bool,
    has_complex: bool,
) -> None:
    if differentiable:
        raise AssertionError("_foreach ops don't support autograd")

    if len(params) == 0:
        return

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

    lr = _to_scalar(lr)

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, exp_avgs, exp_infs, state_steps]  # type: ignore[list-item]
    )
    for (
        grouped_params_,
        grouped_grads_,
        grouped_exp_avgs_,
        grouped_exp_infs_,
        grouped_state_steps_,
    ), _ in grouped_tensors.values():
        grouped_params = cast(list[Tensor], grouped_params_)
        grouped_grads = cast(list[Tensor], grouped_grads_)
        grouped_exp_avgs = cast(list[Tensor], grouped_exp_avgs_)
        grouped_exp_infs = cast(list[Tensor], grouped_exp_infs_)
        grouped_state_steps = cast(list[Tensor], grouped_state_steps_)

        if has_complex:
            _view_as_real(
                grouped_params, grouped_grads, grouped_exp_avgs, grouped_exp_infs
            )

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
            if maximize:
                # Reuse the intermediate memory (grouped_grads) already allocated for maximize
                torch._foreach_add_(grouped_grads, grouped_params, alpha=weight_decay)
            else:
                grouped_grads = torch._foreach_add(  # type: ignore[assignment]
                    grouped_grads, grouped_params, alpha=weight_decay
                )

        # Update biased first moment estimate.
        torch._foreach_lerp_(grouped_exp_avgs, grouped_grads, 1 - beta1)

        # Update the exponentially weighted infinity norm.
        torch._foreach_mul_(grouped_exp_infs, beta2)

        # in this case, we need to introduce a copy of the grads
        # since one has not been introduced previously
        if not maximize and weight_decay == 0:
            grouped_grads = torch._foreach_abs(grouped_grads)  # type: ignore[assignment]
        else:
            torch._foreach_abs_(grouped_grads)

        torch._foreach_add_(grouped_grads, eps)
        torch._foreach_maximum_(grouped_exp_infs, grouped_grads)

        bias_corrections: tuple[Tensor, ...] | list[Tensor]
        if capturable:
            bias_corrections = torch._foreach_pow(beta1, grouped_state_steps)
            # foreach_sub doesn't allow a scalar as the first arg
            torch._foreach_sub_(bias_corrections, 1)
            torch._foreach_div_(bias_corrections, lr)

            denom = torch._foreach_mul(grouped_exp_infs, bias_corrections)
            torch._foreach_addcdiv_(grouped_params, grouped_exp_avgs, denom)
        else:
            bias_corrections = [
                1 - beta1 ** _get_value(step) for step in grouped_state_steps
            ]
            step_size = [(_get_value(lr) / bc) * -1 for bc in bias_corrections]
            torch._foreach_addcdiv_(
                grouped_params, grouped_exp_avgs, grouped_exp_infs, step_size
            )