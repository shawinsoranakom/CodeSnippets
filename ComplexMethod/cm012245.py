def _get_collective_info(
    node: fx.Node,
) -> tuple[str, tuple[int, ...], int, str] | None:
    """Extract (collective_name, pg_ranks, nelems, dtype) from collective node."""
    import torch.distributed as c10d
    from torch.fx.operator_schemas import normalize_function

    if not c10d.is_initialized():
        return None

    target = node.target
    if not isinstance(target, torch._ops.OpOverload):
        return None
    collective_name = target.name().split("::")[-1].split(".")[0]

    opt = normalize_function(
        target,
        args=node.args,
        kwargs=node.kwargs,
        normalize_to_only_use_kwargs=True,
    )
    if opt is None:
        return None
    _, kwargs = opt
    group_name = kwargs.get("group_name", "")

    try:
        from torch.distributed.distributed_c10d import (
            _resolve_process_group,
            get_process_group_ranks,
        )

        pg = _resolve_process_group(group_name)
        pg_ranks = tuple(sorted(get_process_group_ranks(pg)))
    except (RuntimeError, KeyError, ValueError):
        log.debug(
            "PGE: failed to resolve process group for %s", node.name, exc_info=True
        )
        return None

    # Get nelems from input tensor
    val = node.meta.get("val")
    if isinstance(val, torch.Tensor):
        nelems = 1
        for s in val.shape:
            nelems *= int(s)
        dtype = _dtype_to_nccl_str(val.dtype)
    else:
        # Try first arg
        if node.args and isinstance(node.args[0], fx.Node):
            inp_val = node.args[0].meta.get("val")
            if isinstance(inp_val, torch.Tensor):
                nelems = 1
                for s in inp_val.shape:
                    nelems *= int(s)
                dtype = _dtype_to_nccl_str(inp_val.dtype)
            else:
                return None
        else:
            return None

    return (collective_name, pg_ranks, nelems, dtype)