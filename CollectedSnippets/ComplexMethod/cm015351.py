def _multistep_backprop_diff_hyperparams_fn(
    params: Tensor,
    grad: Tensor,
    opt_differentiable_state: dict[str, Any],
    opt_class: type[Optimizer],
    kwargs: dict[str, Any],
    *ignored: Any,
) -> tuple[Tensor, ...]:
    if kwargs["differentiable"] is not True:
        raise AssertionError("Only call this test function when differentiable=True")

    params = params.clone()
    params.grad = grad

    opt_differentiable_state = {
        k: v.clone() if isinstance(v, torch.Tensor) else v
        for k, v in opt_differentiable_state.items()
    }

    # This copy is necessary so the update on line 78 doesn't overwrite the original kwargs values
    kwargs = kwargs.copy()

    # Have to pass in beta1 and beta2 separately
    # so they're passed in as Tensors (not a tuple) and recognized by gradcheck
    if "beta1" in kwargs or "beta2" in kwargs:
        # Prevent just one beta kwarg from being passed in
        if not ("beta1" in kwargs and "beta2" in kwargs):
            raise AssertionError("Both betas should be defined in kwargs")
        kwargs.update({"betas": (kwargs.pop("beta1"), kwargs.pop("beta2"))})

    kwargs.update(
        {k: v.clone() if isinstance(v, torch.Tensor) else v for k, v in kwargs.items()}
    )
    differentiable_kwargs = [
        v for v in kwargs.values() if isinstance(v, torch.Tensor) and v.requires_grad
    ] + (list(kwargs["betas"]) if "betas" in kwargs else [])

    criterion = nn.MSELoss()

    optimizer = opt_class([params], **kwargs)
    optimizer.state[params].update(opt_differentiable_state)

    # Simple x, y pair
    x = torch.tensor([1.0], dtype=torch.float64)
    y = torch.tensor([2.0], dtype=torch.float64)

    for _ in range(2):
        loss = criterion(x * torch.sum(params), y)
        loss.backward(
            inputs=(params,),
            create_graph=True,
        )
        optimizer.step()
        optimizer.zero_grad()

    meta_loss = loss
    meta_loss.backward(inputs=(*differentiable_kwargs,), create_graph=True)

    # Extra check to make sure the test properly computed a gradient for all kwargs
    for kwarg in differentiable_kwargs:
        if kwarg.grad is None:
            raise AssertionError("Expected gradient for kwarg but got None")

    return (
        (meta_loss,)
        + tuple(
            v
            for v in optimizer.state[params].values()
            if isinstance(v, torch.Tensor) and v.requires_grad
        )
        + tuple(differentiable_kwargs)
    )