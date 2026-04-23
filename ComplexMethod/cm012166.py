def estimate_roofline_runtime_ms(node: fx.Node) -> float:
    """Estimate runtime using roofline model (max of compute and memory bound).

    Uses FLOPs for compute-bound estimate if op is in flop_registry,
    and memory bandwidth for memory-bound estimate.
    Returns 0 for view nodes (no cost).
    """
    from torch._inductor.fx_passes.fusion_regions import is_view_node
    from torch.utils._pytree import tree_flatten, tree_map
    from torch.utils._runtime_estimation import get_compute_time, get_transfer_time
    from torch.utils.flop_counter import flop_registry

    if is_view_node(node):
        return 0.0

    def _get_val(n: Any) -> Any:
        if isinstance(n, fx.Node):
            return n.meta.get("val")
        return n

    args = tree_map(_get_val, node.args)
    kwargs = tree_map(_get_val, node.kwargs)
    out = _get_val(node)

    if out is None:
        return 0.0

    flat_args_kwargs, _ = tree_flatten((args, kwargs))
    flat_outs, _ = tree_flatten(out)
    out_dtypes = OrderedSet([t.dtype for t in flat_outs if isinstance(t, torch.Tensor)])

    # Compute time (FLOPs-based, only if op is in flop_registry)
    # May return SymFloat if shapes are symbolic (after flop division)
    compute_ns: float = 0.0
    func_packet = getattr(node.target, "overloadpacket", None)
    if func_packet in flop_registry and len(out_dtypes) == 1:
        compute_ns = get_compute_time(func_packet, args, kwargs, out, out_dtypes.copy())
        # Extract hint from symbolic value if needed
        if isinstance(compute_ns, (torch.SymInt, torch.SymFloat)):
            compute_ns = compute_ns.node.hint if compute_ns.node.has_hint() else 0.0

    # Transfer time (memory bandwidth-based, uses size_hint internally)
    transfer_ns = get_transfer_time(flat_args_kwargs, flat_outs)

    # Roofline: max of compute and transfer, convert ns to ms
    return max(float(compute_ns), float(transfer_ns)) / 1e6