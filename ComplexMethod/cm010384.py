def trace_scan(
    proxy_mode,
    func_overload,
    combine_fn: Callable,
    init: list[torch.Tensor],
    xs: list[torch.Tensor],
    additional_inputs: tuple[torch.Tensor],
):
    from torch._dynamo.utils import clone_input

    with disable_proxy_modes_tracing():
        sample_inits = [clone_input(x_init) for x_init in init]
        sample_inputs = [first_slice_copy(x) for x in xs]
        sample_additional_inputs = [
            clone_input(x) if isinstance(x, torch.Tensor) else x
            for x in additional_inputs
        ]
        combine_graph = reenter_make_fx(combine_fn)(
            *sample_inits, *sample_inputs, *sample_additional_inputs
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

    carry, output = _extract_carry_and_out(outputs, len(init))
    init_fake_tensors: list[torch.Tensor | torch.SymInt | int] = [
        i.clone() for i in init
    ]
    carry_fake_tensors: list[torch.Tensor | torch.SymInt | int] = [
        c.meta["val"] for c in carry
    ]
    check_meta_consistency(
        init_fake_tensors, carry_fake_tensors, "init", "carry", include_contiguity=False
    )

    _, combine_graph_name = unique_graph_id(proxy_mode, prefix="scan_combine_graph")

    proxy_mode.tracer.root.register_module(combine_graph_name, combine_graph)

    args = (combine_graph, init, xs, additional_inputs)
    proxy_args = pytree.tree_map(proxy_mode.tracer.unwrap_proxy, args)
    out_proxy = proxy_mode.tracer.create_proxy(
        "call_function", func_overload, proxy_args, {}, name="scan"
    )

    with disable_proxy_modes_tracing():
        scan_length = xs[0].shape[0]
        fake_carry, fake_outputs = _extract_carry_and_out(
            [o.meta["val"] for o in outputs], len(init)
        )
        out = (
            *fake_carry,
            *(stack_y(t, scan_length) for t in fake_outputs),
        )

    return track_tensor_tree(out, out_proxy, constant=None, tracer=proxy_mode.tracer)