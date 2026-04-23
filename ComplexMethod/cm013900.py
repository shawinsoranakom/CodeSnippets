def _add_global_state_dependencies(
    graph: torch.fx.Graph, node_to_additional_deps: dict[Node, OrderedSet[Node]]
) -> None:
    import torch.amp

    all_nodes = list(graph.nodes)

    # These are targets of the nodes which need to stay in the same relative place in the graph
    global_state_targets = {torch.amp._enter_autocast, torch.amp._exit_autocast}
    all_nodes_dep_on: list[Node] = []

    def prev_cur_nodes(
        all_nodes: list[Node],
    ) -> Generator[tuple[list[Node], Node], None, None]:
        prev_nodes: list[Node] = []
        next_nodes = list(reversed(all_nodes))

        while next_nodes:
            cur_node = next_nodes.pop()
            yield prev_nodes, cur_node
            prev_nodes.append(cur_node)

    for prev_nodes, cur_node in prev_cur_nodes(all_nodes):
        args_unique = _get_flat_args_unique(cur_node, {})
        new_deps = [n for n in all_nodes_dep_on if n not in args_unique]

        if new_deps:
            additional_deps = node_to_additional_deps[cur_node]
            additional_deps.update(new_deps)

        if cur_node.target in global_state_targets:
            additional_deps = node_to_additional_deps[cur_node]
            additional_deps.update(n for n in prev_nodes if n not in args_unique)
            all_nodes_dep_on.append(cur_node)