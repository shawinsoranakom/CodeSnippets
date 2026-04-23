def _single_tensor_asgd(
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
    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for i, param in enumerate(params):
        grad = grads[i]
        grad = grad if not maximize else -grad
        mu = mus[i]
        ax = axs[i]
        eta = etas[i]
        step_t = state_steps[i]

        # If compiling, the compiler will handle cudagraph checks, see note [torch.compile x capturable]
        if not torch.compiler.is_compiling() and capturable:
            capturable_supported_devices = _get_capturable_supported_devices()
            if not (
                param.device.type
                == mu.device.type
                == eta.device.type
                == step_t.device.type
                and param.device.type in capturable_supported_devices
            ):
                raise AssertionError(
                    f"If capturable=True, params, mus, etas, and state_steps must be "
                    f"on supported devices: {capturable_supported_devices}."
                )

        if torch.is_complex(param):
            grad = torch.view_as_real(grad)
            param = torch.view_as_real(param)
            ax = torch.view_as_real(ax)

        # update step
        step_t += 1

        if weight_decay != 0:
            grad = grad.add(param, alpha=weight_decay)

        if capturable:
            param.mul_(1 - lambd * eta)
            param.addcmul_(grad, eta, value=-1)  # update parameter
        else:
            eta_value = _get_value(eta)
            param.mul_(1 - lambd * eta_value)  # decay term
            param.add_(grad, alpha=-eta_value)  # update parameter

        # averaging
        if capturable or mu.item() != 1:
            ax.add_(param.sub(ax).mul_(mu))
        else:
            ax.copy_(param)

        if capturable:
            eta.copy_(lr / ((1 + lambd * lr * step_t) ** alpha))
            mu.copy_(1 / torch.maximum(step_t - t0, torch.ones_like(step_t)))
        else:
            step = _get_value(step_t)
            new_eta = torch.as_tensor(lr / ((1 + lambd * lr * step) ** alpha))
            eta.copy_(new_eta)
            new_mu = torch.as_tensor(1 / max(1, step - t0))
            mu.copy_(new_mu)