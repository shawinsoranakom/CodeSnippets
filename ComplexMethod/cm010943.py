def _single_tensor_rmsprop(
    params: list[Tensor],
    grads: list[Tensor],
    square_avgs: list[Tensor],
    grad_avgs: list[Tensor],
    momentum_buffer_list: list[Tensor],
    state_steps: list[Tensor],
    *,
    lr: float,
    alpha: float,
    eps: float,
    weight_decay: float,
    momentum: float,
    centered: bool,
    maximize: bool,
    differentiable: bool,
    capturable: bool,
    has_complex: bool,
) -> None:
    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for i, param in enumerate(params):
        step = state_steps[i]

        # If compiling, the compiler will handle cudagraph checks, see note [torch.compile x capturable]
        if not torch.compiler.is_compiling() and capturable:
            capturable_supported_devices = _get_capturable_supported_devices()
            if not (
                param.device.type == step.device.type
                and param.device.type in capturable_supported_devices
            ):
                raise AssertionError(
                    f"If capturable=True, params and state_steps must be on supported devices: {capturable_supported_devices}."
                )

        grad = grads[i]
        grad = grad if not maximize else -grad
        square_avg = square_avgs[i]

        step += 1

        if weight_decay != 0:
            grad = grad.add(param, alpha=weight_decay)

        is_complex_param = torch.is_complex(param)
        if is_complex_param:
            param = torch.view_as_real(param)
            grad = torch.view_as_real(grad)
            square_avg = torch.view_as_real(square_avg)

        square_avg.mul_(alpha).addcmul_(grad, grad, value=1 - alpha)

        if centered:
            grad_avg = grad_avgs[i]
            if is_complex_param:
                grad_avg = torch.view_as_real(grad_avg)
            grad_avg.lerp_(grad, 1 - alpha)
            avg = square_avg.addcmul(grad_avg, grad_avg, value=-1).sqrt_()
        else:
            avg = square_avg.sqrt()

        if differentiable:
            avg = avg.add(eps)
        else:
            avg = avg.add_(eps)

        if momentum > 0:
            buf = momentum_buffer_list[i]
            if is_complex_param:
                buf = torch.view_as_real(buf)
            buf.mul_(momentum).addcdiv_(grad, avg)
            param.add_(buf, alpha=-lr)
        else:
            param.addcdiv_(grad, avg, value=-lr)