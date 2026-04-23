def _multi_tensor_rprop(
    params: list[Tensor],
    grads: list[Tensor],
    prevs: list[Tensor],
    step_sizes: list[Tensor],
    state_steps: list[Tensor],
    *,
    step_size_min: float,
    step_size_max: float,
    etaminus: float,
    etaplus: float,
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
        capturable_supported_devices = _get_capturable_supported_devices()
        if not all(
            p.device.type == step.device.type
            and p.device.type in capturable_supported_devices
            for p, step in zip(params, state_steps, strict=True)
        ):
            raise AssertionError(
                f"If capturable=True, params and state_steps must be on supported devices: {capturable_supported_devices}."
            )

    grouped_tensors = Optimizer._group_tensors_by_device_and_dtype(
        [params, grads, prevs, step_sizes, state_steps]  # type: ignore[list-item]
    )
    for (
        grouped_params_,
        grouped_grads_,
        grouped_prevs_,
        grouped_step_sizes_,
        grouped_state_steps_,
    ), _ in grouped_tensors.values():
        grouped_params = cast(list[Tensor], grouped_params_)
        grouped_grads = cast(list[Tensor], grouped_grads_)
        grouped_prevs = cast(list[Tensor], grouped_prevs_)
        grouped_step_sizes = cast(list[Tensor], grouped_step_sizes_)
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

        # Handle complex params
        if has_complex:
            _view_as_real(
                grouped_params, grouped_grads, grouped_prevs, grouped_step_sizes
            )

        signs = torch._foreach_mul(grouped_grads, grouped_prevs)
        if maximize:
            torch._foreach_neg_(signs)

        # At the end of the step, grouped_prevs will contain the current grads, so we reuse
        # grouped_prevs memory instead of creating a new buffer, but, for clarity, we reassign
        # to keep referring to the buffer as grouped_grads.
        torch._foreach_copy_(grouped_prevs, grouped_grads)
        if maximize:
            torch._foreach_neg_(grouped_prevs)
        grouped_grads = grouped_prevs

        torch._foreach_sign_(signs)
        if capturable:
            for sign in signs:
                sign.copy_(torch.where(sign.gt(0), etaplus, sign))
                sign.copy_(torch.where(sign.lt(0), etaminus, sign))
                sign.copy_(torch.where(sign.eq(0), 1, sign))
        else:
            for sign in signs:
                sign[sign.gt(0)] = etaplus
                sign[sign.lt(0)] = etaminus
                sign[sign.eq(0)] = 1

        # update stepsizes with step size updates
        torch._foreach_mul_(grouped_step_sizes, signs)
        for step_size in grouped_step_sizes:
            step_size.clamp_(step_size_min, step_size_max)

        # for dir<0, dfdx=0
        # for dir>=0 dfdx=dfdx
        grouped_grads = list(grouped_grads)
        for i in range(len(grouped_grads)):
            grouped_grads[i].copy_(
                torch.where(signs[i].eq(etaminus), 0, grouped_grads[i])
            )

        # explicitly del signs as it's not used after here to save memory
        del signs

        # update parameters
        grad_signs = [grad.sign() for grad in grouped_grads]
        torch._foreach_addcmul_(
            grouped_params, grad_signs, grouped_step_sizes, value=-1
        )