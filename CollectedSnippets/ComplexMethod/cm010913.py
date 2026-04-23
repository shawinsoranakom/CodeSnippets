def _single_tensor_adagrad(
    params: list[Tensor],
    grads: list[Tensor],
    state_sums: list[Tensor],
    state_steps: list[Tensor],
    grad_scale: Tensor | None,
    found_inf: Tensor | None,
    *,
    lr: float,
    weight_decay: float,
    lr_decay: float,
    eps: float,
    has_sparse_grad: bool,
    maximize: bool,
    differentiable: bool,
    has_complex: bool,
) -> None:
    if grad_scale is not None or found_inf is not None:
        raise AssertionError("Expected grad_scale and found_inf to be None")

    if not torch.jit.is_scripting():
        lr = _to_scalar(lr)

    for param, grad, state_sum, step_t in zip(
        params, grads, state_sums, state_steps, strict=True
    ):
        # update step
        step_t += 1
        step = _get_value(step_t)
        grad = grad if not maximize else -grad

        if weight_decay != 0:
            if grad.is_sparse:
                raise RuntimeError(
                    "weight_decay option is not compatible with sparse gradients"
                )
            grad = grad.add(param, alpha=weight_decay)

        clr = lr / (1 + (step - 1) * lr_decay)

        if grad.is_sparse:
            grad = grad.coalesce()  # the update is non-linear so indices must be unique
            grad_indices = grad._indices()
            grad_values = grad._values()

            state_sum.add_(_make_sparse(grad, grad_indices, grad_values.pow(2)))
            std = state_sum.sparse_mask(grad)
            std_values = std._values().sqrt_().add_(eps)
            param.add_(
                _make_sparse(grad, grad_indices, grad_values / std_values), alpha=-clr
            )
        else:
            is_complex = torch.is_complex(param)
            if is_complex:
                grad = torch.view_as_real(grad)
                state_sum = torch.view_as_real(state_sum)
                param = torch.view_as_real(param)
            state_sum.addcmul_(grad, grad, value=1)
            if differentiable:
                std = state_sum.sqrt() + eps
            else:
                std = state_sum.sqrt().add_(eps)
            param.addcdiv_(grad, std, value=-clr)
            if is_complex:
                param = torch.view_as_complex(param)
                state_sum = torch.view_as_complex(state_sum)