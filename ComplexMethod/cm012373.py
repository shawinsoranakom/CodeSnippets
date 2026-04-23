def propagate_scale_by(nodes_with_chunking_meta: Sequence[Node]) -> None:
    """
    The input is a list of nodes that have chunking metadata.
    The nodes are already sorted in topological order.
    """
    for node in nodes_with_chunking_meta:
        arg_nodes = get_args_of_node_type(node)
        arg_metas = get_chunking_metas(arg_nodes)

        if all(arg_meta is None for arg_meta in arg_metas):
            # should be graph input of the chunking subgraph
            continue

        if log.isEnabledFor(logging.DEBUG):
            print("Propagate scale_by:")
            format_node_with_chunking_meta(node, True)

        assert all(arg_meta is not None for arg_meta in arg_metas), node.format_node()

        # None of the input has scale_by set
        if all(arg_meta.scale_by is None for arg_meta in arg_metas):  # type: ignore[union-attr]
            continue

        target = node.target
        if (
            not isinstance(target, torch._ops.OpOverload)
            or target not in propagate_rules
        ):
            raise CantChunk(
                f"Missing scale_by propagation rule for target {target}: {node.format_node()}"
            )

        if not propagate_rules[target](node):
            raise CantChunk(
                f"scale_by propagate rule for {target} fail: {node.format_node()}"
            )