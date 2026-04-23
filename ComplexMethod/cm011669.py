def is_cudagraph_unsafe_fx_node(fx_node: torch.fx.Node) -> bool:
    """
    Check if an FX node is cudagraph-unsafe.

    This includes:
    - Ops in FORBIDDEN_CUDAGRAPH_OPS (CPU sync, dynamic alloc, etc.)
    - Ops with the cudagraph_unsafe tag
    - Input-dependent unsafe ops (e.g., index_put with boolean indices)
    - Ops with sparse tensor outputs
    """
    target = fx_node.target

    # Check against the forbidden ops set
    if str(target) in FORBIDDEN_CUDAGRAPH_OPS:
        return True

    # Check for cudagraph_unsafe tag
    if (
        isinstance(target, torch._ops.OpOverload)
        and torch._C.Tag.cudagraph_unsafe in target.tags  # type: ignore[attr-defined]
    ):
        return True

    # Check for input-dependent unsafety
    if _fx_node_is_input_dependent_cudagraph_unsafe(fx_node):
        return True

    # Check for sparse tensor outputs
    if (val := fx_node.meta.get("val")) is not None:
        vals = [val] if not isinstance(val, (list, tuple)) else val
        for v in vals:
            if isinstance(v, torch.Tensor) and v.is_sparse:
                return True

    return False