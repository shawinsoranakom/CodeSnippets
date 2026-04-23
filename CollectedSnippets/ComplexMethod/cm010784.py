def remove_suffix(
        cur_graph: fx.Graph, cur_inps: Sequence[torch.Tensor], granularity: int
    ) -> ReproState | None:
        tested: set[int] = set()
        new_graph = fx.Graph()
        env: dict[fx.Node, fx.Node] = {}
        for idx, node in enumerate(cur_graph.nodes):
            new_node = new_graph.node_copy(node, lambda x: env[x])
            if node.op not in ["placeholder", "output"]:
                # If idx is divisible by (granularity * 2), it would have been checked already.
                if (
                    idx % granularity == 0
                    and (idx % (granularity * 2) != 0)
                    and idx not in tested
                ):
                    output_node = new_graph.output((new_node,))
                    if len(new_graph.nodes) < len(cur_graph.nodes) and graph_fails(
                        new_graph, cur_inps
                    ):
                        return ReproState(new_graph, cur_inps)
                    else:
                        tested.add(idx)
                        new_graph.erase_node(output_node)
            env[node] = new_node
        return None