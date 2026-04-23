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