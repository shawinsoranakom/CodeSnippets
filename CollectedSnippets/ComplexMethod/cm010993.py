def _coalescing_manager(
    group: ProcessGroup | None = None,
    device: torch.device | None = None,
    async_ops: bool = False,
):
    """
    Context manager used to coalesce collectives or P2P operations when possible.

    Args:
        group (`ProcessGroup`, optional): The process group to work on. If None,
            the default process group will be used.
        device (`torch.device`, optional): Default is None, set to a device if
            there isn't a `**_coalesced` implementation by the backend.
        async_ops (`bool`, optional): whether the coalesced ops are async ops.

    Examples:
        >>> # xdoctest: +SKIP("no rank")
        >>> # Synchronous ops
        >>> with _coalescing_manager():
        >>>     for i in range(num_colls):
        >>>         dist.all_reduce(tensors[i])
        >>> # Asynchronous ops
        >>> with _coalescing_manager(async_ops=True) as cm:
        >>>     for i in range(num_colls):
        >>>         dist.all_reduce(tensors[i])
        >>> cm.wait()

    .. warning::
       :func:`_coalescing_manager` currently do not support coalescing
       all-reduces with different reduce operators, e.g.  `ReduceOp.SUM` mixed
       with `ReduceOp.PRODUCT`.
    """
    group = group or _get_default_group()
    op_list = _world.pg_coalesce_state.setdefault(group, [])
    if op_list:
        raise ValueError(
            "ProcessGroup has non-empty op list at the start of coalescing"
        )
    if device:
        group._start_coalescing(device)
    cm = _CoalescingManager()
    yield cm
    work = None
    op_list = _world.pg_coalesce_state.pop(group)
    if op_list:
        # Collectives supporting "Fast Path" coalescing are captured.
        # See implementation in corresponding collective APIs.
        # Currently supported:
        # - coalesced `all_reduce`
        # - coalesced `all_gather_into_tensor`
        # - coalesced `reduce_scatter_tensor`
        op0 = op_list[0].op
        if any(op.op is not op0 for op in op_list):
            raise RuntimeError(
                "Coalescing manager requires all collectives to be the same type, "
                f"but got mixed types: {set(op.op.__name__ for op in op_list)}"  # noqa: C401
            )

        if op0 is all_reduce:
            tensors = [op.tensor for op in op_list]
            all_reduce_opts = AllreduceCoalescedOptions()
            all_reduce_opts.reduceOp = not_none(op_list[0].redop)
            all_reduce_opts.asyncOp = async_ops
            work = group.allreduce_coalesced(tensors, all_reduce_opts)
        elif op0 is all_gather_into_tensor:
            inputs = []
            outputs = []
            for op in op_list:
                inputs.append(op.tensor)
                outputs.append(not_none(op.dst_tensor))
            all_gather_opts = AllgatherOptions()
            all_gather_opts.asyncOp = async_ops
            work = group.allgather_into_tensor_coalesced(
                outputs, inputs, all_gather_opts
            )
        elif op0 is reduce_scatter_tensor:
            inputs = []
            outputs = []
            for op in op_list:
                inputs.append(op.tensor)
                outputs.append(not_none(op.dst_tensor))
            reduce_opts = ReduceScatterOptions()
            reduce_opts.reduceOp = not_none(op_list[0].redop)
            reduce_opts.asyncOp = async_ops
            work = group.reduce_scatter_tensor_coalesced(outputs, inputs, reduce_opts)
        else:
            raise AssertionError(
                f"Coalescing manager does not support fast-path coalescing of {op0}, "
                f"yet {op0} is still recorded in op list. This is an internal error of c10d."
            )

    if device:
        # Old style of letting each coll inside the context manager to call into C++ counterpart via python binding
        work = group._end_coalescing(device)

    if async_ops:
        cm.append(work)
    elif (
        work is not None
    ):  # Backward compatible with backends that don't sync at CPP level
        work.wait()