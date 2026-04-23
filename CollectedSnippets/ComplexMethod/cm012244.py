def _get_node_input_shapes_and_strides(
    node: fx.Node,
) -> tuple[tuple[tuple[int, ...], ...], tuple[tuple[int, ...], ...]] | None:
    """Extract input shapes and strides from FX node tensor args.

    Returns (shapes, strides) or None if no tensor args or symbolic dims.
    """
    from torch._inductor.fx_passes.node_runtime_estimation import get_hint

    shapes: list[tuple[int, ...]] = []
    strides: list[tuple[int, ...]] = []
    for arg in node.args:
        if not isinstance(arg, fx.Node):
            continue
        val = arg.meta.get("val")
        if isinstance(val, torch.Tensor):
            resolved_shape = []
            for s in val.shape:
                h = get_hint(s)
                if h is None:
                    return None
                resolved_shape.append(h)
            resolved_stride = []
            for s in val.stride():
                h = get_hint(s)
                if h is None:
                    return None
                resolved_stride.append(h)
            shapes.append(tuple(resolved_shape))
            strides.append(tuple(resolved_stride))
    if not shapes:
        return None
    return tuple(shapes), tuple(strides)