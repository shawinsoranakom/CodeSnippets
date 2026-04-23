def _unwrap_batched(
    batched_outputs: Tensor | tuple[Tensor, ...],
    out_dims: out_dims_t,
    vmap_level: int,
    batch_size: int,
    func: Callable[..., Any],
) -> tuple[Any, ...]:
    flat_batched_outputs, output_spec = tree_flatten(batched_outputs)

    def incompatible_error() -> NoReturn:
        raise ValueError(
            f"vmap({_get_name(func)}, ..., out_dims={out_dims})(<inputs>): "
            f"out_dims is not compatible with the structure of `outputs`. "
            f"out_dims has structure {tree_flatten(out_dims)[1]} but outputs "
            f"has structure {output_spec}."
        )

    flat_out_dims: list[int | None] = []
    if isinstance(batched_outputs, torch.Tensor):
        # Some weird edge case requires us to spell out the following
        # see test_out_dims_edge_case
        if isinstance(out_dims, int):
            flat_out_dims = [out_dims]
        elif isinstance(out_dims, tuple) and len(out_dims) == 1:
            flat_out_dims = list(out_dims)
        elif out_dims is None:
            flat_out_dims = [out_dims]
        else:
            incompatible_error()
    else:
        broadcast_result = _broadcast_to_and_flatten(out_dims, output_spec)
        if broadcast_result is None:
            incompatible_error()
        else:
            flat_out_dims = broadcast_result

    flat_outputs = [
        _maybe_remove_batch_dim(
            _get_name(func), batched_output, vmap_level, batch_size, out_dim
        )
        for batched_output, out_dim in zip(flat_batched_outputs, flat_out_dims)
    ]
    return tree_unflatten(flat_outputs, output_spec)