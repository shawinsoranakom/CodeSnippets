def _multi_tensor_radam(
    params: list[Tensor],
    grads: list[Tensor],
    exp_avgs: list[Tensor],
    exp_avg_sqs: list[Tensor],
    state_steps: list[Tensor],
    *,
    beta1: float,
    beta2: float,
    lr: float,
    weight_decay: float,
    eps: float,
    decoupled_weight_decay: bool,
    differentiable: bool,
    maximize: bool,
    capturable: bool,
    has_complex: bool,
) -> None:
    if len(params) == 0:
        return

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

    lr = _to_scalar(lr)

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, exp_avgs, exp_avg_sqs, state_steps]  # type: ignore[list-item]
    )
    for (
        grouped_params_,
        grouped_grads_,
        grouped_exp_avgs_,
        grouped_exp_avg_sqs_,
        grouped_state_steps_,
    ), _ in grouped_tensors.values():
        grouped_params = cast(list[Tensor], grouped_params_)
        grouped_grads = cast(list[Tensor], grouped_grads_)
        grouped_exp_avgs = cast(list[Tensor], grouped_exp_avgs_)
        grouped_exp_avg_sqs = cast(list[Tensor], grouped_exp_avg_sqs_)
        grouped_state_steps = cast(list[Tensor], grouped_state_steps_)

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

        if has_complex:
            _view_as_real(
                grouped_params, grouped_grads, grouped_exp_avgs, grouped_exp_avg_sqs
            )

        if maximize:
            grouped_grads = torch._foreach_neg(grouped_grads)  # type: ignore[assignment]

        # maximum length of the approximated SMA
        rho_inf = 2 / (1 - beta2) - 1
        # compute the length of the approximated SMA
        bias_correction1: tuple[Tensor, ...] | list[Tensor]
        bias_correction2: tuple[Tensor, ...] | list[Tensor]
        rho_t_list: tuple[Tensor, ...] | list[Tensor]
        if capturable:
            bias_correction1 = torch._foreach_pow(beta2, grouped_state_steps)
            torch._foreach_neg_(bias_correction1)
            torch._foreach_add_(bias_correction1, 1)
            bias_correction2 = torch._foreach_pow(beta2, grouped_state_steps)
            torch._foreach_mul_(bias_correction2, grouped_state_steps)
            torch._foreach_mul_(bias_correction2, 2)
            torch._foreach_div_(bias_correction2, bias_correction1)
            torch._foreach_neg_(bias_correction2)
            torch._foreach_add_(bias_correction2, rho_inf)
            rho_t_list = bias_correction2
        else:
            rho_t_list = [
                rho_inf
                - 2
                * _get_value(step)
                * (beta2 ** _get_value(step))
                / (1 - beta2 ** _get_value(step))
                for step in grouped_state_steps
            ]

        if weight_decay != 0:
            if decoupled_weight_decay:
                torch._foreach_mul_(grouped_params, 1 - lr * weight_decay)
            else:
                # Reuse the intermediate memory (grouped_grads) already allocated for maximize
                if maximize:
                    torch._foreach_add_(
                        grouped_grads, grouped_params, alpha=weight_decay
                    )
                else:
                    grouped_grads = torch._foreach_add(  # type: ignore[assignment]
                        grouped_grads, grouped_params, alpha=weight_decay
                    )

        # Decay the first and second moment running average coefficient
        torch._foreach_lerp_(grouped_exp_avgs, grouped_grads, 1 - beta1)

        torch._foreach_mul_(grouped_exp_avg_sqs, beta2)
        torch._foreach_addcmul_(
            grouped_exp_avg_sqs, grouped_grads, grouped_grads, 1 - beta2
        )

        # Delete the local intermediate since it won't be used anymore to save on peak memory
        del grouped_grads

        if capturable:
            num = torch._foreach_sub(rho_t_list, 4)
            sub2 = torch._foreach_sub(rho_t_list, 2)
            torch._foreach_mul_(num, sub2)
            del sub2
            torch._foreach_mul_(num, rho_inf)
            rho_inf = (rho_inf - 4) * (rho_inf - 2)
            denom = torch._foreach_mul(rho_t_list, rho_inf)
            torch._foreach_div_(num, denom)
            del denom
            torch._foreach_sqrt_(num)

            # TODO(mlazos): we should try and get a foreach_where op https://github.com/pytorch/pytorch/issues/117884
            rect = [
                torch.where(rho_t > 5.0, n, 0.0)
                for n, rho_t in zip(num, rho_t_list, strict=True)
            ]
            del num
            del rho_t_list
            unrect_step_size = [torch.where(rect > 0, 0.0, 1.0) for rect in rect]
            torch._foreach_mul_(unrect_step_size, lr)

            bias_correction1 = torch._foreach_pow(beta1, grouped_state_steps)
            torch._foreach_neg_(bias_correction1)
            torch._foreach_add_(bias_correction1, 1)

            torch._foreach_div_(unrect_step_size, bias_correction1)
            torch._foreach_neg_(unrect_step_size)

            bias_correction2 = torch._foreach_pow(beta2, grouped_state_steps)
            torch._foreach_neg_(bias_correction2)
            torch._foreach_add_(bias_correction2, 1)
            torch._foreach_sqrt_(bias_correction2)
            torch._foreach_mul_(bias_correction2, lr)
            torch._foreach_mul_(bias_correction2, rect)
            del rect
            torch._foreach_neg_(bias_correction2)
            torch._foreach_div_(bias_correction2, bias_correction1)
            del bias_correction1
        else:
            rect = [
                (  # type: ignore[misc]
                    (rho_t - 4)  # type: ignore[arg-type]
                    * (rho_t - 2)
                    * rho_inf
                    / ((rho_inf - 4) * (rho_inf - 2) * rho_t)
                )
                ** 0.5
                if rho_t > 5
                else 0
                for rho_t in rho_t_list
            ]
            unrectified = [0 if rect > 0 else 1.0 for rect in rect]

            bias_correction1 = [
                1 - beta1 ** _get_value(step) for step in grouped_state_steps
            ]
            unrect_step_size = [
                (lr * rect / bc) * -1
                for rect, bc in zip(unrectified, bias_correction1, strict=True)
            ]
            bias_correction2 = [
                ((1 - beta2 ** _get_value(step)) ** 0.5) * (lr * rect / bc) * -1
                for step, rect, bc in zip(
                    grouped_state_steps, rect, bias_correction1, strict=True
                )
            ]

        buffer = torch._foreach_sqrt(grouped_exp_avg_sqs)
        torch._foreach_add_(buffer, eps)
        torch._foreach_div_(buffer, bias_correction2)
        torch._foreach_reciprocal_(buffer)
        torch._foreach_add_(buffer, unrect_step_size)

        # Here, buffer = sqrt(1 - beta2^t) * rect_step_size / (sqrt(v) + eps) + unrect_step_size
        torch._foreach_addcmul_(grouped_params, grouped_exp_avgs, buffer)