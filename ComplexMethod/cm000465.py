async def __create_graph(tx, graph: Graph, user_id: str):
    graphs = [graph] + graph.sub_graphs

    # Auto-increment version for any graph entry (parent or sub-graph) whose
    # (id, version) already exists.  This prevents UniqueViolationError when
    # the copilot re-saves an agent that already exists at the requested version.
    # NOTE: This issues one find_first query per graph entry (N+1 pattern).
    # Sub-graph counts are typically small (< 5), so the overhead is negligible.
    for g in graphs:
        existing = await AgentGraph.prisma(tx).find_first(
            where={"id": g.id},
            order={"version": "desc"},
        )
        if existing and existing.version >= g.version:
            old_version = g.version
            g.version = existing.version + 1
            logger.warning(
                "Auto-incremented graph %s version from %d to %d "
                "(version %d already exists)",
                g.id,
                old_version,
                g.version,
                existing.version,
            )

    await AgentGraph.prisma(tx).create_many(
        data=[
            AgentGraphCreateInput(
                id=graph.id,
                version=graph.version,
                name=graph.name,
                description=graph.description,
                recommendedScheduleCron=graph.recommended_schedule_cron,
                isActive=graph.is_active,
                userId=user_id,
                forkedFromId=graph.forked_from_id,
                forkedFromVersion=graph.forked_from_version,
            )
            for graph in graphs
        ]
    )

    await AgentNode.prisma(tx).create_many(
        data=[
            AgentNodeCreateInput(
                id=node.id,
                agentGraphId=graph.id,
                agentGraphVersion=graph.version,
                agentBlockId=node.block_id,
                constantInput=SafeJson(node.input_default),
                metadata=SafeJson(node.metadata),
            )
            for graph in graphs
            for node in graph.nodes
        ]
    )

    await AgentNodeLink.prisma(tx).create_many(
        data=[
            AgentNodeLinkCreateInput(
                id=str(uuid.uuid4()),
                sourceName=link.source_name,
                sinkName=link.sink_name,
                agentNodeSourceId=link.source_id,
                agentNodeSinkId=link.sink_id,
                isStatic=link.is_static,
            )
            for graph in graphs
            for link in graph.links
        ]
    )