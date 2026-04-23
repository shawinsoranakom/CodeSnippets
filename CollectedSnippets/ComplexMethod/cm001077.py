def json_to_graph(agent_json: dict[str, Any]) -> Graph:
    """Convert agent JSON dict to Graph model.

    Args:
        agent_json: Agent JSON with nodes and links

    Returns:
        Graph ready for saving

    Raises:
        AgentJsonValidationError: If required fields are missing from nodes or links
    """
    nodes = []
    for idx, n in enumerate(agent_json.get("nodes", [])):
        block_id = n.get("block_id")
        if not block_id:
            node_id = n.get("id", f"index_{idx}")
            raise AgentJsonValidationError(
                f"Node '{node_id}' is missing required field 'block_id'"
            )
        node = Node(
            id=n.get("id", str(uuid.uuid4())),
            block_id=block_id,
            input_default=n.get("input_default", {}),
            metadata=n.get("metadata", {}),
        )
        nodes.append(node)

    links = []
    for idx, link_data in enumerate(agent_json.get("links", [])):
        source_id = link_data.get("source_id")
        sink_id = link_data.get("sink_id")
        source_name = link_data.get("source_name")
        sink_name = link_data.get("sink_name")

        missing_fields = []
        if not source_id:
            missing_fields.append("source_id")
        if not sink_id:
            missing_fields.append("sink_id")
        if not source_name:
            missing_fields.append("source_name")
        if not sink_name:
            missing_fields.append("sink_name")

        if missing_fields:
            link_id = link_data.get("id", f"index_{idx}")
            raise AgentJsonValidationError(
                f"Link '{link_id}' is missing required fields: {', '.join(missing_fields)}"
            )

        link = Link(
            id=link_data.get("id", str(uuid.uuid4())),
            source_id=source_id,
            sink_id=sink_id,
            source_name=source_name,
            sink_name=sink_name,
            is_static=link_data.get("is_static", False),
        )
        links.append(link)

    return Graph(
        id=agent_json.get("id", str(uuid.uuid4())),
        version=agent_json.get("version", 1),
        is_active=agent_json.get("is_active", True),
        name=agent_json.get("name", "Generated Agent"),
        description=agent_json.get("description", ""),
        nodes=nodes,
        links=links,
    )