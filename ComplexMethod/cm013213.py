def sample_inputs_cross_entropy(op_info, device, dtype, requires_grad, **kwargs):
    batch_size, num_classes = shape = (2, 3)
    reductions = ("mean", "sum", "none")

    input_shape_and_kwargs: list[tuple[tuple[int, ...], dict[str, Any]]] = [
        (shape, {}),
        ((*shape, 1), {}),
        ((*shape, 1, 2), {}),
        ((*shape, 1, 2, 3), {}),
        *[(shape, dict(reduction=reduction)) for reduction in reductions],
        *[
            (
                shape,
                dict(
                    weight=make_tensor((num_classes,), device=device, dtype=dtype),
                    reduction=reduction,
                ),
            )
            for reduction in reductions
        ],
        (shape, dict(ignore_index=1)),
    ]

    for (input_shape, kwargs), probabilities_target in itertools.product(input_shape_and_kwargs, (False, True)):
        input = make_tensor(input_shape, device=device, dtype=dtype, requires_grad=requires_grad)

        if probabilities_target:
            # ignore_index is not supported for probabilities target
            if "ignore_index" in kwargs:
                continue

            target = make_tensor(
                input_shape,
                low=0,
                high=1,
                device=device,
                dtype=dtype,
                requires_grad=requires_grad,
            )
        else:
            target = make_tensor(
                (batch_size, *input_shape[2:]),
                low=0,
                high=num_classes,
                device=device,
                dtype=torch.long,
            )

            if "ignore_index" in kwargs and torch.all(target == kwargs["ignore_index"]):
                # make sure at least one item in target is not ignored
                target[0] = random.sample(sorted(set(range(num_classes)) - {kwargs["ignore_index"]}), 1)[0]

        yield SampleInput(input, target, **kwargs)