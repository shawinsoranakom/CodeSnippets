def _single_tensor_adafactor(
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
    if grad_scale is not None or found_inf is not None:
        raise AssertionError("Grad scaling should occur outside of optimizer.step()")

    if torch.jit.is_scripting():
        # this assert is due to JIT being dumb and not realizing that the ops below
        # have overloads to handle both float and Tensor lrs, so we just assert it's
        # a float since most people using JIT are using floats
        if not isinstance(lr, float):
            raise AssertionError(f"Expected lr to be a float, but got {type(lr)}")

    else:
        lr = _to_scalar(lr)

    for i, param in enumerate(params):
        grad = grads[i] if not maximize else -grads[i]
        step_t = state_steps[i]
        row_var = row_vars[i]
        col_var = col_vars[i]
        variance = variances[i]
        if eps1 is None:
            eps1 = torch.finfo(param.dtype).eps

        # update step
        step_t += 1
        step_float = step_t.item()

        one_minus_beta2_t = step_float**beta2_decay
        rho_t = min(lr, 1 / (step_float**0.5))
        alpha = max(eps2, param.norm(2).item() / (param.numel() ** 0.5)) * rho_t

        # Perform stepweight decay
        if weight_decay != 0:
            param.mul_(1 - lr * weight_decay)

        if grad.dim() > 1:
            if row_var is None or col_var is None:
                raise AssertionError(
                    "row_var and col_var should be defined when grad is multidimensional"
                )
            # same as (g * g).mean(dim=-1) w/o materializing an intermediate size g
            row_mean = (
                torch.norm(grad, dim=-1, keepdim=True).square_().div_(grad.size(-1))
            )
            row_var.lerp_(row_mean, one_minus_beta2_t)
            # same as (g * g).mean(dim=-2) w/o materializing an intermediate size g
            col_mean = (
                torch.norm(grad, dim=-2, keepdim=True).square_().div_(grad.size(-2))
            )
            col_var.lerp_(col_mean, one_minus_beta2_t)
            var_estimate = row_var @ col_var
            var_estimate.div_(row_var.mean(dim=-2, keepdim=True).clamp_(min=eps1))
        else:
            if variance is None:
                raise AssertionError("variance should be defined when grad is a vector")
            grad_squared = grad * grad
            variance.lerp_(grad_squared, one_minus_beta2_t)
            # avoid writing into variance during update
            var_estimate = variance.clone()

        # square the eps1 as we sqrt after to keep eps1's magnitude
        update = var_estimate.clamp_(min=eps1 * eps1).rsqrt_()
        update.mul_(grad)
        denom = max(1.0, update.norm(2).item() / ((update.numel() ** 0.5) * d))
        param.add_(update, alpha=-alpha / denom)