def _single_tensor_rprop(
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
    for i, param in enumerate(params):
        grad = grads[i]
        grad = grad if not maximize else -grad
        prev = prevs[i]
        step_size = step_sizes[i]
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

        step += 1

        if torch.is_complex(param):
            grad = torch.view_as_real(grad)
            prev = torch.view_as_real(prev)
            param = torch.view_as_real(param)
            step_size = torch.view_as_real(step_size)
        if differentiable:
            sign = grad.mul(prev.clone()).sign()
        else:
            sign = grad.mul(prev).sign()

        if capturable:
            sign.copy_(torch.where(sign.gt(0), etaplus, sign))
            sign.copy_(torch.where(sign.lt(0), etaminus, sign))
            sign.copy_(torch.where(sign.eq(0), 1, sign))
        else:
            sign[sign.gt(0)] = etaplus
            sign[sign.lt(0)] = etaminus
            sign[sign.eq(0)] = 1

        # update stepsizes with step size updates
        step_size.mul_(sign).clamp_(step_size_min, step_size_max)

        # for dir<0, dfdx=0
        # for dir>=0 dfdx=dfdx
        grad = grad.clone(memory_format=torch.preserve_format)
        if capturable:
            grad.copy_(torch.where(sign.eq(etaminus), 0, grad))
        else:
            grad[sign.eq(etaminus)] = 0

        # update parameters
        param.addcmul_(grad.sign(), step_size, value=-1)
        prev.copy_(grad)