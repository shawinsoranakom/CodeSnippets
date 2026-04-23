def _for_each_rank_run_func(
    func: OpOverload | Callable[..., Any],
    ranks: frozenset[int],
    args: Sequence[Any],
    kwargs: dict[str, Any],
    *,
    alias: bool = True,
) -> Any:
    flat_args, args_spec = pytree.tree_flatten((args, kwargs))
    flat_args = [
        a.wait() if isinstance(a, AsyncCollectiveTensor) else a for a in flat_args
    ]

    lm = enabled_local_tensor_mode()
    use_per_rank_rng = lm is not None and len(lm._per_rank_rng_states) > 0

    global_rng_state = None if use_per_rank_rng else _get_rng_state()

    flat_rank_rets = {}

    default_value: Tensor | None = None
    for r in sorted(ranks):
        if use_per_rank_rng:
            if lm is None:
                raise AssertionError
            if r in lm._per_rank_rng_states:
                _set_rng_state(*lm._per_rank_rng_states[r])
        else:
            if global_rng_state is None:
                raise AssertionError
            _set_rng_state(*global_rng_state)

        rank_flat_args = [_map_to_rank_local_val(a, r) for a in flat_args]
        rank_args, rank_kwargs = pytree.tree_unflatten(rank_flat_args, args_spec)
        if func is torch.ops.aten.hash_tensor.default and rank_args[0].numel() == 0:
            # Special case for empty tensors, hash_tensor returns an empty tensor
            rank_ret = torch.empty(0, dtype=torch.uint64, device=rank_args[0].device)
        else:
            rank_ret = func(*rank_args, **rank_kwargs)
        flat_rank_rets[r] = rank_ret

        if use_per_rank_rng:
            if lm is None:
                raise AssertionError
            lm._per_rank_rng_states[r] = _get_rng_state()

        if default_value is None and func is torch.ops.aten.split.Tensor:
            # If split happens over the dimension smaller than the number of chunks
            # it is possible that some ranks will produce shorter lists of chunks.
            # In order to make the result across all ranks of the same length we
            # append empty tensors (zero size on the split dimension).
            tensor = rank_flat_args[0]
            split_dim = 0 if len(rank_flat_args) < 3 else rank_flat_args[2]
            default_value = _zero_sized_like(tensor, split_dim)

    if _is_inplace_op(func):
        alias = False
        # For the in-place ops return self
        ret = args[0]
        if isinstance(func, OpOverload) and torch.Tag.inplace_view in func.tags:
            # Ensure that wrapper tensor size is synchronized with its local tensors
            ret._sync_meta()
    else:
        ret = _combine_rank_results(flat_rank_rets, default_value)

    if alias:
        return return_and_correct_aliasing(func, args, kwargs, ret)
    else:
        return ret