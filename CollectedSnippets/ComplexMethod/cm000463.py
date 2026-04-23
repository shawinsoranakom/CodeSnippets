async def get_sub_graphs(graph: AgentGraph) -> list[AgentGraph]:
    """
    Iteratively fetches all sub-graphs of a given graph, and flattens them into a list.
    This call involves a DB fetch in batch, breadth-first, per-level of graph depth.
    On each DB fetch we will only fetch the sub-graphs that are not already in the list.
    """
    sub_graphs = {graph.id: graph}
    search_graphs = [graph]
    agent_block_id = AgentExecutorBlock().id

    while search_graphs:
        sub_graph_ids = [
            (graph_id, graph_version)
            for graph in search_graphs
            for node in graph.Nodes or []
            if (
                node.AgentBlock
                and node.AgentBlock.id == agent_block_id
                and (graph_id := cast(str, dict(node.constantInput).get("graph_id")))
                and (
                    graph_version := cast(
                        int, dict(node.constantInput).get("graph_version")
                    )
                )
            )
        ]
        if not sub_graph_ids:
            break

        graphs = await AgentGraph.prisma().find_many(
            where={
                "OR": [
                    {
                        "id": graph_id,
                        "version": graph_version,
                        "userId": graph.userId,  # Ensure the sub-graph is owned by the same user
                    }
                    for graph_id, graph_version in sub_graph_ids
                ]
            },
            include=AGENT_GRAPH_INCLUDE,
        )

        search_graphs = [graph for graph in graphs if graph.id not in sub_graphs]
        sub_graphs.update({graph.id: graph for graph in search_graphs})

    return [g for g in sub_graphs.values() if g.id != graph.id]