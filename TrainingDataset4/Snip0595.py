async def create_agent_graph(
    db: Prisma, agent_data: dict, known_blocks: set[str]
) -> tuple[str, int]:
    """Create an AgentGraph and its nodes/links from JSON data."""
    graph_id = agent_data["id"]
    version = agent_data.get("version", 1)

    # Check if graph already exists
    existing_graph = await db.agentgraph.find_unique(
        where={"graphVersionId": {"id": graph_id, "version": version}}
    )
    if existing_graph:
        print(f"  Graph {graph_id} v{version} already exists, skipping")
        return graph_id, version

    print(
        f"  Creating graph {graph_id} v{version}: {agent_data.get('name', 'Unnamed')}"
    )

    # Create the main graph
    await db.agentgraph.create(
        data=AgentGraphCreateInput(
            id=graph_id,
            version=version,
            name=agent_data.get("name"),
            description=agent_data.get("description"),
            instructions=agent_data.get("instructions"),
            recommendedScheduleCron=agent_data.get("recommended_schedule_cron"),
            isActive=agent_data.get("is_active", True),
            userId=AUTOGPT_USER_ID,
            forkedFromId=agent_data.get("forked_from_id"),
            forkedFromVersion=agent_data.get("forked_from_version"),
        )
    )

    # Create nodes
    nodes = agent_data.get("nodes", [])
    for node in nodes:
        block_id = node["block_id"]
        # Ensure the block exists (create placeholder if needed)
        block_exists = await ensure_block_exists(db, block_id, known_blocks)
        if not block_exists:
            print(
                f"    Skipping node {node['id']} - block {block_id} could not be created"
            )
            continue

        await db.agentnode.create(
            data=AgentNodeCreateInput(
                id=node["id"],
                agentBlockId=block_id,
                agentGraphId=graph_id,
                agentGraphVersion=version,
                constantInput=Json(node.get("input_default", {})),
                metadata=Json(node.get("metadata", {})),
            )
        )

    # Create links
    links = agent_data.get("links", [])
    for link in links:
        await db.agentnodelink.create(
            data=AgentNodeLinkCreateInput(
                id=link["id"],
                agentNodeSourceId=link["source_id"],
                agentNodeSinkId=link["sink_id"],
                sourceName=link["source_name"],
                sinkName=link["sink_name"],
                isStatic=link.get("is_static", False),
            )
        )

    # Handle sub_graphs recursively
    sub_graphs = agent_data.get("sub_graphs", [])
    for sub_graph in sub_graphs:
        await create_agent_graph(db, sub_graph, known_blocks)

    return graph_id, version
