def sample_inputs_binary_cross_entropy(op_info, device, dtype, requires_grad, logits=False, **kwargs):
    make = partial(make_tensor, device=device, dtype=dtype)
    # Lower bounds must be greater than 'eps' defined in gradcheck.py::gradgradcheck() -> eps
    # otherwise perturbation calculation causes Tensor value to become negative triggering
    # a device-side hardware assertion
    make_prob = partial(make, low=1e-6, high=1)

    reductions = ("mean", "sum", "none")

    shapes_and_kwargs = [
        *[(shape, None) for shape in ((), (1,), (S,), (S, S), (S, S, S))],
        *[((S, S), dict(reduction=reduction)) for reduction in reductions],
        *[((S, S), dict(reduction=reduction, weight=make((S, S)))) for reduction in reductions],
    ]

    if logits:
        shapes_and_kwargs.extend(
            [((S, S), dict(reduction=reduction, pos_weight=make((S,), low=0))) for reduction in reductions]
        )

    for shape, kwargs in shapes_and_kwargs:
        yield SampleInput(
            (make if logits else make_prob)(shape, requires_grad=requires_grad),
            args=(make_prob(shape, requires_grad=requires_grad),),
            kwargs=kwargs,
        )