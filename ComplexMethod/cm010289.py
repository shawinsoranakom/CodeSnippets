def _replace_unbacked_bindings(gm: torch.fx.GraphModule) -> None:
    """
    When we run an interpreter-based pass over a GraphModule, execution of data-dependent operators
    will produce example values with new unbacked symbols. To track that the new/old symbols are equivalent,
    we used to rely on the unbacked_renamings mapping. This led to problematic metadata where the unbacked_bindings
    keys mapped new symbols (u2) to paths containing old symbols (u0) in the example values, or worse, backed symbols
    or constants (e.g. if the original unbacked was replaced/specialized). Additionally this created problems with
    de/serialized programs, since we didn't comprehensively serialize ShapeEnv/unbacked renamings/node bindings.

    This pass attempts a simpler way of handling these for export, by throwing away the previously computed bindings, and re-running
    the pattern match used in compute_unbacked_bindings. This ensures we keep the original symbols contained in the example values,
    or delete bindings if they've been replaced/specialized.
    """
    from torch._export.utils import _get_shape_env_from_gm
    from torch.fx.experimental.symbolic_shapes import _free_unbacked_symbols_with_path
    from torch.utils._sympy.symbol import symbol_is_type, SymT

    if (shape_env := _get_shape_env_from_gm(gm)) is None:
        return

    base_unbacked_symbols = {
        symbol
        for symbol in shape_env.var_to_range
        if symbol_is_type(symbol, (SymT.UNBACKED_INT, SymT.UNBACKED_FLOAT))
        and symbol not in shape_env.unbacked_renamings
    }
    for node in gm.graph.nodes:
        node.meta.pop("unbacked_bindings", None)
        if (val := node.meta.get("val")) is not None and (
            unbacked_bindings := _free_unbacked_symbols_with_path(
                val,
                (),
                shape_env=shape_env,
                pending=base_unbacked_symbols,
                simplify=True,
            )
        ):
            node.meta["unbacked_bindings"] = unbacked_bindings