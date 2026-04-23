def _single_tensor_nadam(
    params: list[Tensor],
    grads: list[Tensor],
    exp_avgs: list[Tensor],
    exp_avg_sqs: list[Tensor],
    mu_products: list[Tensor],
    state_steps: list[Tensor],
    *,
    beta1: float,
    beta2: float,
    lr: float,
    weight_decay: float,
    momentum_decay: float,
    eps: float,
    decoupled_weight_decay: bool,
    maximize: bool,
    capturable: bool,
    differentiable: bool,
    has_complex: bool,
) -> None:
    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for i, param in enumerate(params):
        grad = grads[i] if not maximize else -grads[i]
        exp_avg = exp_avgs[i]
        exp_avg_sq = exp_avg_sqs[i]
        mu_product = mu_products[i]
        step_t = state_steps[i]

        if torch.is_complex(param):
            param = torch.view_as_real(param)
            grad = torch.view_as_real(grad)
            exp_avg = torch.view_as_real(exp_avg)
            exp_avg_sq = torch.view_as_real(exp_avg_sq)

        # If compiling, the compiler will handle cudagraph checks, see note [torch.compile x capturable]
        if not torch.compiler.is_compiling() and capturable:
            capturable_supported_devices = _get_capturable_supported_devices()
            if not (
                param.device.type == mu_product.device.type == step_t.device.type
                and param.device.type in capturable_supported_devices
            ):
                raise AssertionError(
                    f"If capturable=True, params, mu_products and state_steps must be "
                    f"on supported devices: {capturable_supported_devices}."
                )

        # update step
        step_t += 1

        if capturable:
            step = step_t
        else:
            step = _get_value(step_t)

        bias_correction2 = 1 - beta2**step

        if weight_decay != 0:
            if decoupled_weight_decay:
                # Perform stepweight decay
                param.mul_(1 - lr * weight_decay)
            else:
                grad = grad.add(param, alpha=weight_decay)

        # calculate the momentum cache \mu^{t} and \mu^{t+1}
        mu = beta1 * (1.0 - 0.5 * (0.96 ** (step * momentum_decay)))
        mu_next = beta1 * (1.0 - 0.5 * (0.96 ** ((step + 1) * momentum_decay)))

        # update mu_product
        mu_product *= mu

        # decay the first and second moment running average coefficient
        exp_avg.lerp_(grad, 1 - beta1)
        exp_avg_sq.mul_(beta2).addcmul_(grad, grad, value=1 - beta2)
        denom = exp_avg_sq.div(bias_correction2).sqrt()

        if differentiable or capturable:
            denom = denom.add(eps)
            # Make autograd track the operations
            # by updating the grad and exp_avg directly and not using the
            # scalar "value" argument of addcdiv.
            mu_product_next = mu_product * mu_next
            grad = grad * (-lr * (1.0 - mu) / (1.0 - mu_product))
            exp_avg = exp_avg * (-lr * mu_next / (1.0 - mu_product_next))
            param.addcdiv_(grad, denom)
            param.addcdiv_(exp_avg, denom)
        else:
            mu_product_next = _get_value(mu_product) * mu_next
            denom.add_(eps)
            param.addcdiv_(
                grad, denom, value=(-lr * (1.0 - mu) / (1.0 - _get_value(mu_product)))
            )
            param.addcdiv_(
                exp_avg,
                denom,
                value=cast(float, (-lr * mu_next) / (1.0 - mu_product_next)),
            )