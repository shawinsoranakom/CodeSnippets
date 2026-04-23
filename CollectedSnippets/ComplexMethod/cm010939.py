def _multi_tensor_nadam(
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
            p.device.type == mp.device.type == step.device.type
            and p.device.type in capturable_supported_devices
            for p, mp, step in zip(params, mu_products, state_steps, strict=True)
        ):
            raise AssertionError(
                "If capturable=True, "
                "params, mu_products, and state_steps must be on supported devices: "
                f"{capturable_supported_devices}."
            )

    lr = _to_scalar(lr)

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, exp_avgs, exp_avg_sqs, mu_products, state_steps]  # type: ignore[list-item]
    )
    for (
        grouped_params_,
        grouped_grads_,
        grouped_exp_avgs_,
        grouped_exp_avg_sqs_,
        grouped_mu_products_,
        grouped_state_steps_,
    ), _ in grouped_tensors.values():
        grouped_params = cast(list[Tensor], grouped_params_)
        grouped_grads = cast(list[Tensor], grouped_grads_)
        grouped_exp_avgs = cast(list[Tensor], grouped_exp_avgs_)
        grouped_exp_avg_sqs = cast(list[Tensor], grouped_exp_avg_sqs_)
        grouped_mu_products = cast(list[Tensor], grouped_mu_products_)
        grouped_state_steps = cast(list[Tensor], grouped_state_steps_)

        # handle complex
        if has_complex:
            _view_as_real(
                grouped_params, grouped_grads, grouped_exp_avgs, grouped_exp_avg_sqs
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
            if decoupled_weight_decay:
                # Perform stepweight decay
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

        exp_avg_sq_sqrt = torch._foreach_sqrt(grouped_exp_avg_sqs)

        bias_correction_sqrt: tuple[Tensor, ...] | list[Tensor]
        mus: tuple[Tensor, ...] | list[Tensor]
        mu_nexts: tuple[Tensor, ...] | list[Tensor]
        if capturable:
            # mus will be beta1 * (1 - 0.5 * 0.96 ** (step * momentum_decay))
            exponent = torch._foreach_mul(grouped_state_steps, momentum_decay)
            mus = torch._foreach_pow(0.96, exponent)
            torch._foreach_mul_(mus, -0.5)
            torch._foreach_add_(mus, 1.0)
            torch._foreach_mul_(mus, beta1)

            # mu_nexts will be beta1 * (1 - 0.5 * 0.96 ** ((step + 1) * momentum_decay))
            torch._foreach_add_(exponent, momentum_decay)
            mu_nexts = torch._foreach_pow(0.96, exponent)
            torch._foreach_mul_(mu_nexts, -0.5)
            torch._foreach_add_(mu_nexts, 1.0)
            torch._foreach_mul_(mu_nexts, beta1)

            # save peak memory as we don't need exponent anymore
            del exponent

            bias_correction_sqrt = torch._foreach_pow(beta2, grouped_state_steps)
            # foreach_sub doesn't allow a scalar as the first arg
            torch._foreach_sub_(bias_correction_sqrt, 1.0)
            torch._foreach_neg_(bias_correction_sqrt)
            torch._foreach_sqrt_(bias_correction_sqrt)
        else:
            bias_correction_sqrt = [
                (1 - beta2 ** _get_value(step)) ** 0.5 for step in grouped_state_steps
            ]
            mus = [
                beta1 * (1.0 - 0.5 * (0.96 ** (_get_value(step) * momentum_decay)))
                for step in grouped_state_steps
            ]
            mu_nexts = [
                beta1
                * (1.0 - 0.5 * (0.96 ** ((_get_value(step) + 1) * momentum_decay)))
                for step in grouped_state_steps
            ]

        # update mu_products
        torch._foreach_mul_(grouped_mu_products, mus)

        torch._foreach_div_(exp_avg_sq_sqrt, bias_correction_sqrt)
        torch._foreach_add_(exp_avg_sq_sqrt, eps)

        # explicitly delete bias_correction refs to save memory
        del bias_correction_sqrt

        if capturable:
            # Build up the step_size multiplier for grad, reusing mus' memory
            torch._foreach_sub_(mus, 1.0)
            torch._foreach_mul_(mus, lr)
            # foreach_sub doesn't allow a scalar as the first arg
            denom = torch._foreach_sub(grouped_mu_products, 1.0)
            torch._foreach_neg_(denom)
            torch._foreach_div_(mus, denom)
            # - lr * (1 - mu) / (1 - mu_product)
            step_size_grads = mus
            # explicitly delete denom to save memory
            del denom

            # Build up the step_size multiplier for exp_avg, reusing mu_nexts' memory
            denom = torch._foreach_mul(grouped_mu_products, mu_nexts)
            torch._foreach_mul_(mu_nexts, lr)
            # foreach_sub doesn't allow a scalar as the first arg, but it's okay because
            # we need a negative here anyway
            torch._foreach_sub_(denom, 1.0)
            torch._foreach_div_(mu_nexts, denom)
            # - lr * mu_next / (1 - mu_product * mu_next)
            step_size_expavg = mu_nexts
            # explicitly delete denom to save memory
            del denom

            # we cannot inplace into step_size_grads cuz it is a list of ScalarTensors
            # and mul'ing with grouped_grads will result in a list of bigger Tensors
            numerator = torch._foreach_mul(step_size_grads, grouped_grads)
            torch._foreach_addcmul_(numerator, step_size_expavg, grouped_exp_avgs)

            # finally, update params
            torch._foreach_addcdiv_(grouped_params, numerator, exp_avg_sq_sqrt)
        else:
            step_size_grads = _stack_if_compiling(
                [
                    (_get_value(lr) * (1.0 - mu) / (1.0 - _get_value(mu_product))) * -1
                    for mu_product, mu in zip(grouped_mu_products, mus, strict=True)
                ]
            )
            step_size_expavg = _stack_if_compiling(
                [
                    (
                        _get_value(lr)
                        * mu_next
                        / (1.0 - _get_value(mu_product) * mu_next)
                    )
                    * -1
                    for mu_product, mu_next in zip(
                        grouped_mu_products, mu_nexts, strict=True
                    )
                ]
            )

            torch._foreach_addcdiv_(
                grouped_params,
                grouped_grads,
                exp_avg_sq_sqrt,
                step_size_grads,  # type: ignore[arg-type]
            )
            torch._foreach_addcdiv_(
                grouped_params,
                grouped_exp_avgs,
                exp_avg_sq_sqrt,
                step_size_expavg,  # type: ignore[arg-type]
            )