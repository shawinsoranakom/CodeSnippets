def _single_tensor_adadelta(
    params: list[Tensor],
    grads: list[Tensor],
    square_avgs: list[Tensor],
    acc_deltas: list[Tensor],
    state_steps: list[Tensor],
    *,
    lr: float,
    rho: float,
    eps: float,
    weight_decay: float,
    maximize: bool,
    differentiable: bool,
    capturable: bool,
    has_complex: bool,
) -> None:
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

    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for param, grad, square_avg, acc_delta, step in zip(
        params, grads, square_avgs, acc_deltas, state_steps, strict=True
    ):
        step += 1
        grad = grad if not maximize else -grad

        if weight_decay != 0:
            grad = grad.add(param, alpha=weight_decay)

        if torch.is_complex(param):
            square_avg = torch.view_as_real(square_avg)
            acc_delta = torch.view_as_real(acc_delta)
            grad = torch.view_as_real(grad)

        square_avg.mul_(rho).addcmul_(grad, grad, value=1 - rho)
        std = square_avg.add(eps).sqrt_()
        delta = acc_delta.add(eps).sqrt_()
        if differentiable:
            delta = delta.clone()
        delta.div_(std).mul_(grad)
        acc_delta.mul_(rho).addcmul_(delta, delta, value=1 - rho)

        if torch.is_complex(param):
            delta = torch.view_as_complex(delta)
        param.add_(delta, alpha=-lr)