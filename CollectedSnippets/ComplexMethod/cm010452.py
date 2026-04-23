def broadcast_tensors(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    tensors = new_kwargs.pop("tensors")
    if len(tensors) == 0:
        raise ValueError("broadcast_tensors(): expected at least one tensor input")
    if len(tensors) == 1:
        return tensors[0]

    outs = []
    broadcast_shape = torch.broadcast_shapes(*(t.shape for t in tensors))
    # Pull out the first NJT. If broadcast_shapes() worked, the nested ints are compatible.
    njt = next(t for t in tensors if isinstance(t, NestedTensor))
    for t in tensors:
        if t.is_nested:
            outs.append(t.broadcast_to(broadcast_shape))
        elif t.dim() < len(broadcast_shape):
            outs.append(
                NestedTensor(t.broadcast_to(njt._values.shape), **extract_kwargs(njt))
            )
        else:
            raise ValueError(
                "broadcast_tensors(): broadcasting nested tensors with dense tensors of equal "
                "or higher dim is not currently supported"
            )

    return tuple(outs)