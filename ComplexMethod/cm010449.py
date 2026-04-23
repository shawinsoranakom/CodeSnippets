def _softmax_default(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    if isinstance(new_kwargs["dim"], tuple):
        raise RuntimeError(
            "softmax(): not supported for dimensions of type 'tuple' for NestedTensor"
        )

    inp = new_kwargs.pop("input")

    (
        new_kwargs["dim"],
        reduce_on_batch,
        reduce_on_ragged,
        _reduce_on_non_batch,
    ) = _wrap_jagged_dims(
        inp.dim(),
        (new_kwargs["dim"],),
        "softmax",
        inp._ragged_idx,
    )

    if reduce_on_batch:
        raise RuntimeError(
            "softmax(): not supported when reducing across the batch dimension for NestedTensor"
        )

    if reduce_on_ragged and inp._ragged_idx > 1:
        raise RuntimeError(
            "softmax(): not supported when reducing along the ragged dimension for ragged_idx > 1 for NestedTensor"
        )

    if reduce_on_ragged and inp._lengths is not None:
        raise RuntimeError(
            "softmax(): not supported where lengths is not None "
            + "if reducing across the ragged dimension for NestedTensor"
        )

    new_kwargs["dim"] = new_kwargs["dim"][
        0
    ]  # torch.softmax takes in the reduction dimension as an integer

    if reduce_on_ragged:
        padded_softmax_values = torch.nn.functional.softmax(
            torch.ops.aten._jagged_to_padded_dense_forward(
                inp._values.reshape(
                    inp._values.shape[0], -1
                ),  # values are required to be 2D tensors for j2pd
                [inp._offsets],
                max_lengths=[inp._max_seqlen],  # max length of ragged dimension
                padding_value=float("-inf"),  # e^-inf = 0
            ),
            dim=inp._ragged_idx,
        )

        softmax_values = torch.ops.aten._padded_dense_to_jagged_forward(
            padded_softmax_values,
            [inp._offsets],
            total_L=inp._values.shape[
                0
            ],  # providing this parameter helps avoid a GPU/CPU sync
        ).reshape(
            -1, *inp._values.shape[1:]
        )  # expand softmax_values back to original shape (inp._values.shape)

        return NestedTensor(softmax_values, **extract_kwargs(inp))

    return NestedTensor(func(inp._values, **new_kwargs), **extract_kwargs(inp))