def control_deps_op_lowering(additional_deps, subgraph_fn, *args):
    """
    Lower control_deps_op by ensuring dependencies are realized and tracking them.

    The control_deps_op HOP makes dependencies explicit in the graph. During lowering:
    1. Realize all additional dependencies to ensure they're computed
    2. Execute the target operation normally
    3. Track the dependencies for the scheduler
    """
    # Realize all additional dependencies
    dep_names = []
    for dep in additional_deps:
        if not isinstance(dep, IRNode):
            continue

        dep.realize()
        dep_names.append(dep.get_name())

    original_args = V.graph.current_node.args
    arg_offset = 2  # first two args (additional_deps, subgraph)
    assert len(args) + arg_offset == len(original_args)

    operation_len = len(V.graph.operations)
    assert len(subgraph_fn.graph_module.graph.find_nodes(op="placeholder")) == len(args)

    # Process subgraph nodes using the shared helper
    output = process_subgraph_nodes(subgraph_fn.graph_module, list(args))

    assert additional_deps

    # some operators, like wait_tensor, just return their input,
    # so its more robust to add dep to the operation itself,
    # otherwise you can have a cycle of
    # a = coll
    # b = control_deps(a, mm, ...)
    # c = control_deps(b, wait, ...)
    # if c == a, then you have a cycle.
    for op in V.graph.operations[operation_len:]:
        for dep_name in dep_names:
            op_name = op.operation_name
            assert op_name is not None
            V.graph.additional_buffer_deps[op_name].add(dep_name)

    return output