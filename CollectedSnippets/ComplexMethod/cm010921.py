def _multi_tensor_adafactor(
    params: list[Tensor],
    grads: list[Tensor],
    # If grad is 1-dimensional (aka a vector), there is no factorization necessary
    # so row_var and col_var will be None while variance will be filled.
    # Contrarily, for a grad with multiple dimensions, we will factor along the last
    # 2 dimensions, and so row_var and col_var will be filled and variance will be None.
    row_vars: list[Tensor | None],
    col_vars: list[Tensor | None],
    variances: list[Tensor | None],
    state_steps: list[Tensor],
    grad_scale: Tensor | None,
    found_inf: Tensor | None,
    *,
    d: float,
    lr: Tensor | float,
    beta2_decay: float,
    weight_decay: float,
    eps1: float | None,
    eps2: float,
    maximize: bool,
    has_complex: bool,
) -> None:
    if len(params) == 0:
        return

    if grad_scale is not None or found_inf is not None:
        raise AssertionError("Grad scaling should occur outside of optimizer.step()")

    lr = _to_scalar(lr)

    grouped_tensors = _group_tensors_by_device_dtype_and_is_multidim(
        [params, grads, row_vars, col_vars, variances, state_steps]  # type: ignore[list-item]
    )
    for (_, dtype, is_multidim), (
        (
            device_params_,
            device_grads_,
            device_row_vars_,
            device_col_vars_,
            device_variances_,
            device_state_steps_,
        )
    ) in grouped_tensors.items():
        device_params = cast(list[Tensor], device_params_)
        device_grads = cast(list[Tensor], device_grads_)
        device_state_steps = cast(list[Tensor], device_state_steps_)
        if eps1 is None:
            if dtype is None:
                raise AssertionError(
                    "dtype is needed to compute eps1 when eps1 is unset"
                )
            eps1 = torch.finfo(dtype).eps

        if TYPE_CHECKING:
            assert device_state_steps[0] is not None

        if maximize:
            device_grads = torch._foreach_neg(device_grads)  # type: ignore[assignment]

        # Update steps
        # If steps are on CPU, foreach will fall back to the slow path, which is a for-loop calling t.add(1) over
        # and over. 1 will then be wrapped into a Tensor over and over again, which is slower than if we just
        # wrapped it once now. The alpha is required to assure we go to the right overload.
        if not torch.compiler.is_compiling() and device_state_steps[0].is_cpu:
            torch._foreach_add_(
                device_state_steps, torch.tensor(1.0, device="cpu"), alpha=1.0
            )
        else:
            torch._foreach_add_(device_state_steps, 1.0)

        one_minus_beta2_ts = []
        beta2_ts = []
        rho_ts = []
        for s in device_state_steps:
            one_minus_beta2_ts.append(s.item() ** beta2_decay)
            beta2_ts.append(1 - s.item() ** beta2_decay)
            rho_ts.append(min(lr, 1 / (s.item() ** 0.5)))

        alphas = [
            max(eps2, p.norm(2).item() / (p.numel() ** 0.5)) * r
            for p, r in zip(device_params, rho_ts, strict=True)
        ]

        # Perform stepweight decay
        if weight_decay != 0:
            torch._foreach_mul_(device_params, 1 - lr * weight_decay)

        if is_multidim:
            device_row_vars = cast(list[Tensor], device_row_vars_)
            device_col_vars = cast(list[Tensor], device_col_vars_)
            if device_row_vars[0] is None or device_col_vars[0] is None:
                raise AssertionError(
                    "row_var and col_var should be defined when grad is multidimensional"
                )
            # same as (g * g).mean(dim=-1) w/o materializing an intermediate size g
            row_means = [
                torch.norm(grad, dim=-1, keepdim=True) for grad in device_grads
            ]
            torch._foreach_mul_(row_means, row_means)
            torch._foreach_div_(row_means, [grad.size(-1) for grad in device_grads])
            torch._foreach_lerp_(device_row_vars, row_means, one_minus_beta2_ts)
            del row_means

            # same as (g * g).mean(dim=-2) w/o materializing an intermediate size g
            col_means = [
                torch.norm(grad, dim=-2, keepdim=True) for grad in device_grads
            ]
            torch._foreach_mul_(col_means, col_means)
            torch._foreach_div_(col_means, [grad.size(-2) for grad in device_grads])
            torch._foreach_lerp_(device_col_vars, col_means, one_minus_beta2_ts)
            del col_means

            var_estimates = [
                row_var @ col_var
                for row_var, col_var in zip(
                    device_row_vars, device_col_vars, strict=True
                )
            ]
            row_var_means = [
                row_var.mean(dim=-2, keepdim=True) for row_var in device_row_vars
            ]
            torch._foreach_clamp_min_(row_var_means, eps1)
            torch._foreach_div_(var_estimates, row_var_means)
            del row_var_means
        else:
            device_variances = cast(list[Tensor], device_variances_)
            if device_variances[0] is None:
                raise AssertionError("variance should be defined when grad is a vector")

            grads_squared = torch._foreach_mul(device_grads, device_grads)
            torch._foreach_lerp_(device_variances, grads_squared, one_minus_beta2_ts)
            del grads_squared

            # avoid writing into variance during update
            var_estimates = [v.clone() for v in device_variances]

        # square the eps1 as we sqrt after to keep eps1's magnitude
        torch._foreach_clamp_min_(var_estimates, eps1 * eps1)
        torch._foreach_rsqrt_(var_estimates)
        torch._foreach_mul_(var_estimates, device_grads)
        updates = var_estimates

        alphas = [
            -a / (max(1.0, update.norm(2).item() / ((update.numel() ** 0.5) * d)))
            for a, update in zip(alphas, updates, strict=True)
        ]
        torch._foreach_mul_(updates, alphas)
        torch._foreach_add_(device_params, updates)