def build_subgraph_input_mapping(
    tx: "InstructionTranslator",
    p_args: tuple[Any, ...],
    flat_vts: list[tuple[InputTag, VariableTracker]],
) -> list[LiftedArgOrigin]:
    """Build a mapping that records the origin of each lifted arg for a subgraph.

    On a cache hit, we stamp out a new invoke_subgraph call and need to
    reconstruct its argument list in the correct order. Each lifted arg
    (p_args[2:], skipping body_node and body_name) comes from one of:

    - LiftedUserArg: a user argument (intermediate activation or explicit input)
    - LiftedCapturedSource: a captured variable (e.g. a weight or parameter)
    - LiftedSyntheticObject: a TorchScriptObject with a SyntheticLocalSource
    - LiftedBoundSymbol: a SymInt already bound as a graph input
    """
    proxy_node_to_idx: dict[torch.fx.Node, int] = {}
    idx = 0
    for tag, vt in flat_vts:
        if tag in (InputTag.TENSOR, InputTag.SYMNODE):
            node = vt.as_proxy().node
            if node not in proxy_node_to_idx:
                proxy_node_to_idx[node] = idx
                idx += 1

    subgraph_input_mapping: list[LiftedArgOrigin] = []
    for outer_proxy in p_args[2:]:
        matched_idx = proxy_node_to_idx.get(outer_proxy.node, -1)
        if matched_idx >= 0:
            subgraph_input_mapping.append(LiftedUserArg(matched_idx))
        else:
            grapharg = outer_proxy.node.meta.get("grapharg", None)
            source = grapharg.source if grapharg is not None else None
            # SymInt freevars must reuse the existing symbolic proxy rather
            # than resolving via source.get_value() (which returns the
            # concrete int). They appear as either:
            # - placeholder nodes with grapharg.example being a SymInt
            # - call_function nodes (e.g. sym_size_int) with no grapharg
            # In both cases, store the sympy expression and look it up in
            # bound_symbols during stamp-out.
            example = (
                grapharg.example
                if grapharg is not None
                else outer_proxy.node.meta.get("example_value", None)
            )
            if isinstance(example, torch.SymInt):
                subgraph_input_mapping.append(LiftedBoundSymbol(example.node.expr))
                continue
            assert source is not None, (
                f"Freevar has no source: node.op={outer_proxy.node.op} "
                f"node.name={outer_proxy.node.name} -- this likely means a "
                f"function argument was not included in the proxy matching"
            )
            if isinstance(source, SyntheticLocalSource):
                ctor_info = tx.output.synthetic_source_ctor_info.get(source)
                if ctor_info is not None:
                    ctor_fn, ctor_args, ctor_arg_sources = ctor_info
                    subgraph_input_mapping.append(
                        LiftedSyntheticObject(ctor_fn, ctor_args, ctor_arg_sources)
                    )
                    continue
            subgraph_input_mapping.append(LiftedCapturedSource(source))
    return subgraph_input_mapping