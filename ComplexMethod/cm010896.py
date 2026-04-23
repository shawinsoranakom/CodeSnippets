def _single_tensor_radam(
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
    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for i, param in enumerate(params):
        grad = grads[i] if not maximize else -grads[i]
        exp_avg = exp_avgs[i]
        exp_avg_sq = exp_avg_sqs[i]
        step_t = state_steps[i]

        # If compiling, the compiler will handle cudagraph checks, see note [torch.compile x capturable]
        if not torch.compiler.is_compiling() and capturable:
            capturable_supported_devices = _get_capturable_supported_devices()
            if not (
                param.device.type == step_t.device.type
                and param.device.type in capturable_supported_devices
            ):
                raise AssertionError(
                    f"If capturable=True, params and state_steps must be on supported devices: {capturable_supported_devices}."
                )

        if torch.is_complex(param):
            param = torch.view_as_real(param)
            grad = torch.view_as_real(grad)
            exp_avg = torch.view_as_real(exp_avg)
            exp_avg_sq = torch.view_as_real(exp_avg_sq)

        # update step
        step_t += 1
        step = step_t if capturable else _get_value(step_t)

        if weight_decay != 0:
            if decoupled_weight_decay:
                param.mul_(1 - lr * weight_decay)
            else:
                grad = grad.add(param, alpha=weight_decay)

        # Decay the first and second moment running average coefficient
        exp_avg.lerp_(grad, 1 - beta1)
        exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)

        bias_correction1 = 1 - beta1**step
        bias_correction2 = 1 - beta2**step

        # correcting bias for the first moving moment
        bias_corrected_exp_avg = exp_avg / bias_correction1

        # maximum length of the approximated SMA
        rho_inf = 2 / (1 - beta2) - 1
        # compute the length of the approximated SMA
        rho_t = rho_inf - 2 * step * (beta2**step) / bias_correction2

        def _compute_rect():
            return (
                (rho_t - 4)
                * (rho_t - 2)
                * rho_inf
                / ((rho_inf - 4) * (rho_inf - 2) * rho_t)
            ) ** 0.5

        def _compute_adaptive_lr():
            exp_avg_sq_sqrt = exp_avg_sq.sqrt()
            if differentiable:
                exp_avg_sq_sqrt = exp_avg_sq_sqrt.add(eps)
            else:
                exp_avg_sq_sqrt = exp_avg_sq_sqrt.add_(eps)

            return (bias_correction2**0.5) / exp_avg_sq_sqrt

        # Compute the variance rectification term and update parameters accordingly
        if capturable:
            update = torch.where(
                rho_t > 5.0, _compute_rect() * _compute_adaptive_lr(), 1.0
            )
            param.add_(bias_corrected_exp_avg * lr * update, alpha=-1.0)
        else:
            if rho_t > 5.0:
                param.add_(
                    bias_corrected_exp_avg
                    * lr
                    * _compute_adaptive_lr()
                    * _compute_rect(),
                    alpha=-1.0,
                )
            else:
                param.add_(bias_corrected_exp_avg * lr, alpha=-1.0)