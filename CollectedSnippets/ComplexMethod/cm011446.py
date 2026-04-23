def _mark_sharding(
    gm: GraphModule,
    graph_signature: ExportGraphSignature,
    mesh: DeviceMesh,
    parameter_placements: dict[str, Placement],
) -> dict[Node, OpSpec]:
    """
    Mark the sharding strategy for each node in the graph module.
    """
    placement_strategies: dict[Node, OpSpec] = _mark_tensor_parallel_shardings(
        gm,
        graph_signature,
        mesh,
        parameter_placements,
    )

    for node in gm.graph.nodes:
        if node.op == "placeholder":
            if node not in placement_strategies:
                placement_strategies[node] = _create_placement_strategy(
                    node, mesh, placements=(Replicate(),)
                )
            node.meta["sharding"] = placement_strategies[node]
        elif node.op == "call_function":
            if node.target is operator.getitem:
                input_nodes = node.all_input_nodes
                if len(input_nodes) != 1:
                    raise AssertionError(
                        f"non-compute op only support one input now, found node: {node} "
                        f"with length of inputs: {len(node.args)}"
                    )
                arg_strategy = placement_strategies[input_nodes[0]]
                placement_strategies[node] = _create_placement_strategy(
                    node,
                    mesh,
                    placements=arg_strategy.output_spec.placements,
                    input_specs=_get_input_node_specs(node, placement_strategies),
                )
                node.meta["sharding"] = placement_strategies[node]
            else:
                op_schema = _get_op_schema(node, placement_strategies)

                # get DTensor specs for inputs and outputs
                sharding_propagator = DTensor._op_dispatcher.sharding_propagator
                if (
                    op_schema.op not in sharding_propagator.op_strategy_funcs
                    and op_schema.op not in sharding_propagator.op_to_rules
                    and op_schema.op
                    not in sharding_propagator.op_single_dim_strategy_funcs
                ):
                    # Mark all as replicated
                    output_sharding = _generate_default_output_sharding(
                        node,
                        mesh,
                        op_schema,
                    )
                else:
                    output_sharding = DTensor._op_dispatcher.sharding_propagator.propagate_op_sharding(  # type: ignore[assignment]
                        op_schema,
                    )
                placement_strategies[node] = OpSpec(
                    # pyrefly: ignore [bad-argument-type]
                    output_specs=_get_output_spec_from_output_sharding(output_sharding),
                    # pyrefly: ignore [missing-attribute]
                    input_specs=output_sharding.redistribute_schema.args_spec
                    # pyrefly: ignore [missing-attribute]
                    if output_sharding.redistribute_schema is not None
                    else _get_input_node_specs(node, placement_strategies),
                )
                node.meta["sharding"] = placement_strategies[node]
        elif node.op == "output":
            node.meta["sharding"] = None
        else:
            raise RuntimeError(f"op code {node.op} not supported")
    return placement_strategies