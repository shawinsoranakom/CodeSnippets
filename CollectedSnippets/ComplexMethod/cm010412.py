def trace_associative_scan(
    proxy_mode,
    func_overload,
    combine_fn: Callable,
    xs: list[torch.Tensor],
    additional_inputs: tuple[torch.Tensor],
):
    from torch._dynamo.utils import clone_input

    with disable_proxy_modes_tracing():
        sample_xs = [first_slice_copy(x) for x in itertools.chain(xs, xs)]
        sample_additional_inputs = [
            clone_input(x) if isinstance(x, torch.Tensor) else x
            for x in additional_inputs
        ]
        combine_graph = reenter_make_fx(combine_fn)(
            *sample_xs, *sample_additional_inputs
        )

    outputs = None
    for node in combine_graph.graph.nodes:
        if node.op == "output":
            if outputs is not None:
                raise AssertionError("found multiple output nodes in combine_graph")
            if len(node.args) != 1:
                raise AssertionError(
                    f"expected output node to have 1 arg, got {len(node.args)}"
                )
            outputs = node.args[0]

    if outputs is None:
        raise AssertionError("no output node found in combine_graph")
    outputs = pytree.tree_leaves(outputs)
    if len(outputs) != len(xs):
        raise AssertionError(
            f"expected combine_fn to return {len(xs)} results but got {len(outputs)}"
        )

    xs_fake_tensors: list[torch.Tensor | torch.SymInt | int] = [
        first_slice_copy(x) for x in xs
    ]
    output_fake_tensors: list[torch.Tensor | torch.SymInt | int] = [
        c.meta["val"] for c in outputs
    ]
    check_meta_consistency(
        xs_fake_tensors, output_fake_tensors, "init", "carry", include_contiguity=False
    )

    _, combine_graph_name = unique_graph_id(
        proxy_mode, prefix="associative_scan_combine_graph"
    )

    proxy_mode.tracer.root.register_module(combine_graph_name, combine_graph)

    args = (combine_graph, xs, additional_inputs)
    proxy_args = pytree.tree_map(proxy_mode.tracer.unwrap_proxy, args)
    out_proxy = proxy_mode.tracer.create_proxy(
        "call_function", func_overload, proxy_args, {}, name="associative_scan"
    )

    with disable_proxy_modes_tracing():
        out = tuple(aten.clone(x) for x in xs)

    return track_tensor_tree(out, out_proxy, constant=None, tracer=proxy_mode.tracer)