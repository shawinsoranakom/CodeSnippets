def trace_cond(proxy_mode, func_overload, pred, true_fn, false_fn, operands):
    if not isinstance(operands, (list, tuple)):
        raise AssertionError(
            f"Cond operands must be a list or tuple of tensors and SymInts {operands}"
        )

    true_graph = reenter_make_fx(true_fn)(*operands)
    false_graph = reenter_make_fx(false_fn)(*operands)

    true_outs = []
    false_outs = []
    for node in true_graph.graph.nodes:
        if node.op == "output":
            true_outs.extend(node.args)

    for node in false_graph.graph.nodes:
        if node.op == "output":
            false_outs.extend(node.args)

    flat_true_outs = pytree.arg_tree_leaves(*true_outs)
    flat_false_outs = pytree.arg_tree_leaves(*false_outs)
    if len(flat_true_outs) != len(flat_false_outs):
        raise torch._dynamo.exc.CondOpArgsMismatchError(
            f"Expected to return same number of outputs but got:"
            f"\n  true branch returns {len(flat_true_outs)} item(s)"
            f"\n  false branch returns {len(flat_false_outs)} item(s)"
        )

    i, true_name = unique_graph_id(proxy_mode, prefix="true_graph")

    false_name = f"false_graph_{i}"
    if hasattr(proxy_mode.tracer.root, false_name):
        raise AssertionError(
            f"proxy_mode.tracer.root already has attribute {false_name}"
        )

    proxy_mode.tracer.root.register_module(true_name, true_graph)
    proxy_mode.tracer.root.register_module(false_name, false_graph)

    args = (pred, true_graph, false_graph, operands)

    proxy_args = pytree.tree_map(proxy_mode.tracer.unwrap_proxy, args)

    out_proxy = proxy_mode.tracer.create_proxy(
        "call_function", func_overload, proxy_args, {}
    )

    out = func_overload(pred, true_graph, false_graph, operands)

    return track_tensor_tree(out, out_proxy, constant=None, tracer=proxy_mode.tracer)