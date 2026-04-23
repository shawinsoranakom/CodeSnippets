def _foreach_map(subgraph, *args, **kwargs):
    """
    This lowers an invocation of foreach_map
    The way this works is that an arbitrary N-arg func is provided by the user, looped over by the
    polyfill with the same semantics as a foreach op (a loop applying an n-ary function to n args)
    and then traced into a subgraph by dynamo.
    This code allows us to inline the subgraph into the main graph lowering using the PontwiseSubgraphLowering.
    The graph outputs represent the vertically fused sequence of ops, and then register_operation_list
    below registers the buffers as horizontally fuseable in the scheduler.
    """
    from .subgraph_lowering import PointwiseSubgraphLowering

    inputs = args

    gm = subgraph.graph_module
    pw_subgraph = PointwiseSubgraphLowering(gm, root_graph_lowering=V.graph)
    with V.set_graph_handler(pw_subgraph):  # type: ignore[arg-type]
        pw_subgraph.run(*inputs)

    sub_outputs = pw_subgraph.graph_outputs
    # group outputs by device and register as foreach
    assert sub_outputs  # mypy lol
    groups = group_foreach_args(sub_outputs)

    outputs = [None] * len(sub_outputs)
    for (device, use_foreach), group in groups.items():
        operation_list: list[str] = []
        for (
            output_ind,
            output,
        ) in group:
            outputs[output_ind] = output

            if V.graph.has_feature(device, BackendFeature.FOREACH) and use_foreach:
                output.realize()
                operation_list.append(output.get_operation_name())

        if operation_list:
            V.graph.register_operation_list(operation_list)

    assert all(x is not None for x in outputs)
    return outputs