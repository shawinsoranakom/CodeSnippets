def _reassign_ids(
        graph: BaseGraph,
        user_id: str,
        graph_id_map: dict[str, str],
    ):
        # Reassign Graph ID
        if graph.id in graph_id_map:
            graph.id = graph_id_map[graph.id]

        # Reassign Node IDs
        id_map = {node.id: str(uuid.uuid4()) for node in graph.nodes}
        for node in graph.nodes:
            node.id = id_map[node.id]

        # Reassign Link IDs
        for link in graph.links:
            if link.source_id in id_map:
                link.source_id = id_map[link.source_id]
            if link.sink_id in id_map:
                link.sink_id = id_map[link.sink_id]

        # Reassign User IDs for agent blocks
        for node in graph.nodes:
            if node.block_id != AgentExecutorBlock().id:
                continue
            node.input_default["user_id"] = user_id
            node.input_default.setdefault("inputs", {})
            if (
                graph_id := node.input_default.get("graph_id")
            ) and graph_id in graph_id_map:
                node.input_default["graph_id"] = graph_id_map[graph_id]