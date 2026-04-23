def _multi_tensor_asgd(
    params: list[Tensor],
    grads: list[Tensor],
    axs: list[Tensor],
    mus: list[Tensor],
    etas: list[Tensor],
    state_steps: list[Tensor],
    *,
    lambd: float,
    lr: float,
    t0: float,
    alpha: float,
    weight_decay: float,
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
        capturable_supported_devices = _get_capturable_supported_devices(
            supports_xla=False
        )
        if not all(
            p.device.type == mu.device.type == eta.device.type == step.device.type
            and p.device.type in capturable_supported_devices
            for p, mu, eta, step in zip(params, mus, etas, state_steps, strict=True)
        ):
            raise AssertionError(
                f"If capturable=True, params, mus, etas, and state_steps must be on "
                f"supported devices: {capturable_supported_devices}."
            )

    lr = _to_scalar(lr)

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, axs, mus, etas, state_steps]  # type: ignore[list-item]
    )
    for (device, _), (
        (
            grouped_params_,
            grouped_grads_,
            grouped_axs_,
            grouped_mus_,
            grouped_etas_,
            grouped_state_steps_,
        ),
        _,
    ) in grouped_tensors.items():
        grouped_params = cast(list[Tensor], grouped_params_)
        grouped_grads = cast(list[Tensor], grouped_grads_)
        grouped_axs = cast(list[Tensor], grouped_axs_)
        grouped_mus = cast(list[Tensor], grouped_mus_)
        grouped_etas = cast(list[Tensor], grouped_etas_)
        grouped_state_steps = cast(list[Tensor], grouped_state_steps_)

        if has_complex:
            _view_as_real(grouped_params, grouped_grads, grouped_axs)

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

        # intermediate = grad + param * lambd
        intermediate: tuple[Tensor, ...] | list[Tensor]
        if weight_decay != 0:
            if maximize:
                torch._foreach_add_(grouped_grads, grouped_params, alpha=weight_decay)
                intermediate = grouped_grads
            else:
                intermediate = torch._foreach_add(
                    grouped_grads, grouped_params, alpha=weight_decay
                )

            torch._foreach_add_(intermediate, grouped_params, alpha=lambd)
        else:
            intermediate = torch._foreach_add(
                grouped_grads, grouped_params, alpha=lambd
            )

        # update param
        # param * (1 - lambd * eta) - eta * grad
        # => param - param * lambd * eta - eta * grad
        # => param - eta * intermediate
        torch._foreach_addcmul_(grouped_params, intermediate, grouped_etas, value=-1)
        del intermediate

        # update grouped_axs
        # averaging: ax = ax + mu * (param - ax)
        # Note (mlazos): We can't use lerp here since it requires weight to be float64
        # and our grouping code requires dtypes to match for all tensors in a group (and it should, since
        # we use the mus in other places)
        # all dtypes need to match, so we could introduce a cast in a loop
        # but since this only adds one additional kernel launch, this looks like the cleaner
        # and faster solution
        intermediate = torch._foreach_sub(grouped_params, grouped_axs)
        torch._foreach_addcmul_(grouped_axs, intermediate, grouped_mus)
        del intermediate

        new_etas: tuple[Tensor, ...] | list[Tensor]
        new_mus: tuple[Tensor, ...] | list[Tensor]
        if capturable:
            # update grouped_mus
            new_mus = torch._foreach_sub(grouped_state_steps, t0)
            torch._foreach_maximum_(new_mus, 1.0)
            torch._foreach_reciprocal_(new_mus)
            torch._foreach_copy_(grouped_mus, new_mus)
            del new_mus

            # update eta = lr / ((1 + lambd * lr * step)^alpha)
            new_etas = torch._foreach_mul(grouped_state_steps, lambd)
            torch._foreach_mul_(new_etas, lr)
            torch._foreach_add_(new_etas, 1)
            torch._foreach_pow_(new_etas, alpha)
            torch._foreach_reciprocal_(new_etas)
            torch._foreach_mul_(new_etas, lr)
            torch._foreach_copy_(grouped_etas, new_etas)
        else:
            new_etas = [
                torch.as_tensor(lr / ((1 + lambd * lr * step) ** alpha), device=device)
                for step in grouped_state_steps
            ]
            new_mus = [
                torch.as_tensor(1 / max(1, _get_value(step) - t0), device=device)
                for step in grouped_state_steps
            ]
            torch._foreach_copy_(grouped_etas, new_etas)
            torch._foreach_copy_(grouped_mus, new_mus)