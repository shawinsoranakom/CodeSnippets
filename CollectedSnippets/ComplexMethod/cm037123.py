def _merge_empty_only_subgraphs(
    node_to_subgraph_id: dict[fx.Node, int],
    split_op_graphs: list[int],
) -> None:
    """
    Merge a partition that only contains an empty allocation op into the
    previous partition. This avoids generating standalone empty submodules,
    which can lead to empty cudagraph captures.
    """

    nodes_by_subgraph_id: dict[int, list[fx.Node]] = defaultdict(list)
    for node, subgraph_id in node_to_subgraph_id.items():
        nodes_by_subgraph_id[subgraph_id].append(node)

    splitting_subgraphs = set(split_op_graphs)
    prev_non_splitting_subgraph_id: int | None = None

    max_subgraph_id = max(node_to_subgraph_id.values(), default=-1)
    for subgraph_id in range(max_subgraph_id + 1):
        nodes = nodes_by_subgraph_id.get(subgraph_id, [])
        if not nodes:
            continue

        is_non_splitting_subgraph = subgraph_id not in splitting_subgraphs
        is_empty_only_subgraph = len(nodes) == 1 and _is_empty_allocation_node(nodes[0])
        merged = False

        if is_empty_only_subgraph and prev_non_splitting_subgraph_id is not None:
            # Safety check: don't move allocation before any input producer.
            empty_node = nodes[0]
            if all(
                input_node.op == "placeholder"
                or node_to_subgraph_id[input_node] <= prev_non_splitting_subgraph_id
                for input_node in empty_node.all_input_nodes
            ):
                node_to_subgraph_id[empty_node] = prev_non_splitting_subgraph_id
                merged = True

        if not merged and is_non_splitting_subgraph:
            prev_non_splitting_subgraph_id = subgraph_id