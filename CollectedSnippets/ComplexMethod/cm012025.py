def estimate_nccl_collective_runtime_from_fx_node(
    fx_node: torch.fx.Node,
    override_size: int | None = None,
    use_nccl_estimator: bool = True,
) -> float:
    """
    Returns estimated NCCL collective runtime in nanoseconds (ms).

    The following heuristics are copied from https://github.com/NVIDIA/nccl/blob/master/src/graph/tuning.cc.
    We aim to estimate the runtime as accurately as possible.

    Assumptions:
    - only ring algorithm (NCCL_ALGO_RING) is used
    - only Low-Latency protocol (NCCL_PROTO_LL) is used, i.e. Simple or LL128 is not used
    - 8 gpus per node  # TODO: Need to find a way to get accurate "gpus per node" and "# nodes" info.
    - collective is one of: allreduce, reducescatter, allgather
    """
    from torch.distributed.distributed_c10d import _get_group_size_by_name

    if fx_node.target is torch.ops._c10d_functional.all_to_all_single.default:
        # TODO(ivankobzarev): Temporarily disabled - NCCL estimator returns internal error.
        # for all_to_all during inductor compilation. Falls back to heuristic estimation.
        use_nccl_estimator = False

    if override_size is None:
        tensor_storage_size_bytes = estimate_fx_collective_size(fx_node)
    else:
        tensor_storage_size_bytes = override_size

    assert not isinstance(fx_node.target, str)
    opt_args_kwargs = normalize_function(
        fx_node.target,
        args=fx_node.args,
        kwargs=fx_node.kwargs,
        normalize_to_only_use_kwargs=True,
    )
    assert opt_args_kwargs is not None
    args, kwargs = opt_args_kwargs

    group_name = kwargs["group_name"]
    group_size = _get_group_size_by_name(group_name)
    assert isinstance(fx_node.target, torch._ops.OpOverload)
    coll = get_collective_type_from_kernel_name(fx_node.target.name())

    def _nccl_estimate() -> float | None:
        # TODO: Refactor with estimate_nccl_collective_runtime_nccl_estimator
        from torch.distributed.distributed_c10d import _resolve_process_group, Backend

        pg = _resolve_process_group(group_name)
        if torch.distributed.distributed_c10d.get_backend(pg) == Backend.FAKE:
            # nccl estimator requires real process group
            return None

        device = torch.device("cuda")
        try:
            backend = pg._get_backend(device)
        except RuntimeError:
            return None
        if not backend.supports_time_estimate:
            return None

        flat_args, flat_args_pytree_spec = pytree.tree_flatten((args, kwargs))

        def _tensor(size, dtype, device) -> torch.Tensor:  # type: ignore[no-untyped-def]
            return torch.empty(
                size if override_size is None else [override_size],
                dtype=dtype,
                device=device,
            )

        def to_real_tensor(e: Any) -> Any:
            if isinstance(e, torch.fx.Node):
                return to_real_tensor(e.meta["val"])
            if isinstance(e, torch.Tensor):
                return _tensor([get_fx_node_size_numel(e.size())], e.dtype, e.device)
            return e

        flat_args = [to_real_tensor(a) for a in flat_args]
        real_args, real_kwargs = pytree.tree_unflatten(flat_args, flat_args_pytree_spec)

        fn = fx_node.target
        assert isinstance(fn, torch._ops.OpOverload)
        with torch.distributed._time_estimator(
            group=pg, device=device
        ) as time_estimator:
            w = fn(*real_args, **real_kwargs)
            # Coalesced collectives return a list of tensors
            if isinstance(w, (list, tuple)):
                for t in w:
                    torch.ops._c10d_functional.wait_tensor.default(t)
            else:
                torch.ops._c10d_functional.wait_tensor.default(w)
        est_time_us = time_estimator.estimated_time
        # -1000 constant is NCCL return in case of error during estimations.
        # Observed it for all_to_all estimations.
        if est_time_us < 0:
            return None
        est_time_ms = est_time_us / 1e3
        return est_time_ms

    if use_nccl_estimator:
        est_time_ms = _nccl_estimate()
        if est_time_ms is not None:
            return est_time_ms

    return estimate_nccl_collective_runtime_impl(
        tensor_storage_size_bytes, group_size, coll
    )