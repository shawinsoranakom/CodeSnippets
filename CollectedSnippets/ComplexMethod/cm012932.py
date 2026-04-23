def add_loggers_to_model(
    gm: GraphModule,
    node_to_instrument_inputs_to_ref_node_name: dict[Node, tuple[str, str]],
    node_to_instrument_outputs_to_ref_node_name: dict[Node, tuple[str, str]],
    logger_cls: Callable,
    model_name: str,
) -> GraphModule:
    """
    Takes the graph of gm, adds loggers to the output
    of each node in nodes_to_instrument. Returns a GraphModule with the new
    graph.
    """

    new_graph = Graph()
    env: dict[str, Any] = {}

    def load_arg(a):
        return map_arg(a, lambda node: env[node.name])

    for node in gm.graph.nodes:
        if node.op == "output":
            new_graph.output(map_arg(get_normalized_nth_input(node, gm, 0), load_arg))
            continue

        if (node in node_to_instrument_inputs_to_ref_node_name) or (
            node in node_to_instrument_outputs_to_ref_node_name
        ):
            fqn = _maybe_get_fqn(node, gm)

            if node in node_to_instrument_inputs_to_ref_node_name:
                ref_name, ref_node_type = node_to_instrument_inputs_to_ref_node_name[
                    node
                ]
                # Ops such add and mul are special because either
                # one or two of the first two arguments can be tensors,
                # and if one argument is a tensor it can be first or
                # second (x + 1 versus 1 + x).
                arg_indices_to_log = get_arg_indices_of_inputs_to_log(node)
                for node_arg_idx in arg_indices_to_log:
                    node_arg = get_normalized_nth_input(node, gm, node_arg_idx)
                    if type(node_arg) is Node:
                        # create a single input logger
                        prev_node = env[node_arg.name]
                        env[node_arg.name] = _insert_logger_after_node(
                            prev_node,
                            gm,
                            logger_cls,
                            "_ns_logger_",
                            node.name,
                            model_name,
                            ref_name,
                            ref_node_type,
                            NSSingleResultValuesType.NODE_INPUT.value,
                            index_within_arg=0,
                            index_of_arg=node_arg_idx,
                            fqn=fqn,
                        )
                    elif (
                        type(node_arg) is torch.fx.immutable_collections.immutable_list
                    ):
                        # create N input loggers, one for each node
                        for arg_idx, arg in enumerate(node_arg):  # type: ignore[var-annotated, arg-type]
                            prev_node = env[arg.name]
                            env[prev_node.name] = _insert_logger_after_node(
                                prev_node,
                                gm,
                                logger_cls,
                                "_ns_logger_",
                                node.name,
                                model_name,
                                ref_name,
                                ref_node_type,
                                NSSingleResultValuesType.NODE_INPUT.value,
                                index_within_arg=arg_idx,
                                index_of_arg=node_arg_idx,
                                fqn=fqn,
                            )

            # ensure env is populated with base node
            # Note: runs for both inputs and outputs
            env[node.name] = new_graph.node_copy(node, load_arg)

            if node in node_to_instrument_outputs_to_ref_node_name:
                ref_name, ref_node_type = node_to_instrument_outputs_to_ref_node_name[
                    node
                ]
                # add the logger after the base node
                env[node.name] = _insert_logger_after_node(
                    env[node.name],
                    gm,
                    logger_cls,
                    "_ns_logger_",
                    node.name,
                    model_name,
                    ref_name,
                    ref_node_type,
                    NSSingleResultValuesType.NODE_OUTPUT.value,
                    index_within_arg=0,
                    index_of_arg=0,
                    fqn=fqn,
                )

        else:
            env[node.name] = new_graph.node_copy(node, load_arg)

    new_gm = GraphModule(gm, new_graph)
    return new_gm