def _single_tensor_adamax(
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
    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for i, param in enumerate(params):
        grad = grads[i]
        grad = grad if not maximize else -grad
        exp_avg = exp_avgs[i]
        exp_inf = exp_infs[i]
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

        # update step
        step_t += 1

        if weight_decay != 0:
            grad = grad.add(param, alpha=weight_decay)

        if torch.is_complex(param):
            param = torch.view_as_real(param)
            grad = torch.view_as_real(grad)
            exp_avg = torch.view_as_real(exp_avg)
            exp_inf = torch.view_as_real(exp_inf)

        # Update biased first moment estimate.
        exp_avg.lerp_(grad, 1 - beta1)
        # Update the exponentially weighted infinity norm.
        if not differentiable:
            torch.maximum(
                exp_inf.mul_(beta2),
                grad.abs().add_(eps),
                out=exp_inf,
            )
        else:
            norm_buf = torch.cat(
                [exp_inf.mul_(beta2).unsqueeze(0), grad.abs().add_(eps).unsqueeze_(0)],
                0,
            )
            exp_inf.copy_(torch.amax(norm_buf, 0, keepdim=False))

        if capturable:
            # why jump through extra hoops and negate bias_correction? check out #121238
            # once fixed, we should use bias_correction with addcdiv value=-1 for readability
            neg_bias_correction = beta1**step_t - 1
            neg_bias_correction.div_(lr)
            denom = exp_inf * neg_bias_correction
            param.addcdiv_(exp_avg, denom)
        else:
            bias_correction = 1 - beta1 ** _get_value(step_t)
            clr = lr / bias_correction

            param.addcdiv_(exp_avg, exp_inf, value=-clr)