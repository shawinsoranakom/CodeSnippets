def lower_pointwise_subgraph(
    subgraph: ir.Subgraph, inputs: list[InputDescriptor]
) -> Callable[_P, Any]:
    # Lower subgraph to ir.Pointwise nodes
    def fake_inner_fn(loop_idx: int, input_idx: int) -> ir.Expr | ir.TensorBox | None:
        return ops.placeholder(input_idx)

    graph_inputs = [
        ir.Pointwise.create(
            device=desc.device,
            dtype=desc.dtype,
            inner_fn=functools.partial(fake_inner_fn, input_idx=i),
            ranges=[],
        )
        for i, desc in enumerate(inputs)
    ]
    gm = subgraph.graph_module
    pw_subgraph = PointwiseSubgraphLowering(gm, root_graph_lowering=V.graph)
    with V.set_graph_handler(pw_subgraph):  # type: ignore[arg-type]
        pw_subgraph.run(*graph_inputs)

    # Combine multiple pointwise computations into a single graph module
    # Do this by tracing through each individually and doing CSE
    tracer = torch.fx.Tracer()
    tracer.graph = torch.fx.Graph(tracer_cls=tracer.__class__)
    trace_ops = SimpleCSEHandler(TracingOpsHandler(tracer, len(inputs)))
    assert pw_subgraph.graph_outputs is not None

    with V.set_ops_handler(trace_ops):
        output_irs = []

        for out_var in pw_subgraph.graph_outputs:
            assert isinstance(out_var, ir.TensorBox), type(out_var)
            assert out_var.get_size() == []
            assert isinstance(out_var.data, ir.StorageBox)
            assert isinstance(out_var.data.data, ir.Pointwise)

            idx = ()
            ir_out = out_var.data.data.inner_fn(idx)

            output_irs.append(ir_out)

        ops.output(*output_irs)

    lowered_gm = torch.fx.GraphModule({}, tracer.graph)

    def inner_fn(*args: _P.args, **kwargs: _P.kwargs) -> Any:
        return lowered_gm(V.get_ops_handler(), *args, **kwargs)

    return inner_fn