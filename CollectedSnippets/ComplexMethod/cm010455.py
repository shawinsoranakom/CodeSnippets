def to_padded_tensor_default(func, *args, **kwargs):
    _, new_kwargs = normalize_function(  # type: ignore[misc]
        func, args=args, kwargs=kwargs, normalize_to_only_use_kwargs=True
    )

    inp = new_kwargs.pop("input")

    if inp._lengths is not None:
        raise RuntimeError(
            "to_padded_tensor(): not supported for nested tensors with holes"
        )

    # TODO: Handle the rest of output_size
    output_size = new_kwargs["output_size"]
    if output_size is not None:
        max_seq_len = output_size[inp._ragged_idx]
    else:
        max_seq_len = (
            inp._max_seqlen
            if inp._max_seqlen_tensor is not None
            else inp._values.size(0)
        )

    # only 2D values with ragged packed dim=0 is supported by the underlying FBGEMM
    # kernel so do shape gymnastics if needed
    values = inp.values()
    if inp._ragged_idx > 1:
        values = values.transpose(inp._ragged_idx - 1, 0)
    values_shape = values.shape
    if values.dim() > 2:
        values = values.flatten(start_dim=1)
    elif values.dim() == 1:
        values = values.unsqueeze(-1)

    # NB: The CUDA kernel for jagged -> padded dense conversion does not support
    # integer / bool types; work around this by casting to half.
    is_bool = values.dtype is torch.bool
    if is_bool and values.is_cuda:
        values = values.to(torch.half)
    padded_out = torch.ops.aten._jagged_to_padded_dense_forward(
        values,
        [inp._offsets],
        [max_seq_len],
        new_kwargs["padding"],
    )
    if is_bool and padded_out.is_cuda:
        padded_out = padded_out.to(torch.bool)

    # shape gymnastics part 2
    if len(values_shape) > 2:
        padded_out = padded_out.unflatten(-1, values_shape[1:])
    elif len(values_shape) == 1:
        padded_out = padded_out.squeeze(-1)
    if inp._ragged_idx > 1:
        padded_out = padded_out.transpose(inp._ragged_idx, 1)

    return padded_out