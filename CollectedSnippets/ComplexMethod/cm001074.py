async def get_all_relevant_agents_for_generation(
    user_id: str,
    search_query: str | None = None,
    exclude_graph_id: str | None = None,
    include_library: bool = True,
    include_marketplace: bool = True,
    max_library_results: int = 15,
    max_marketplace_results: int = 10,
) -> list[AgentSummary]:
    """Fetch relevant agents from library and/or marketplace.

    Searches both user's library and marketplace by default.
    Explicitly mentioned UUIDs in the search query are always looked up.

    Args:
        user_id: The user ID
        search_query: Search term to find relevant agents (user's goal/description)
        exclude_graph_id: Optional graph ID to exclude (prevents circular references)
        include_library: Whether to search user's library (default True)
        include_marketplace: Whether to also search marketplace (default True)
        max_library_results: Max library agents to return (default 15)
        max_marketplace_results: Max marketplace agents to return (default 10)

    Returns:
        List of AgentSummary with full schemas (both library and marketplace agents)
    """
    agents: list[AgentSummary] = []
    seen_graph_ids: set[str] = set()

    if search_query:
        mentioned_uuids = extract_uuids_from_text(search_query)
        for graph_id in mentioned_uuids:
            if graph_id == exclude_graph_id:
                continue
            agent = await get_library_agent_by_graph_id(user_id, graph_id)
            agent_graph_id = agent.get("graph_id") if agent else None
            if agent and agent_graph_id and agent_graph_id not in seen_graph_ids:
                agents.append(agent)
                seen_graph_ids.add(agent_graph_id)
                logger.debug(
                    f"Found explicitly mentioned agent: {agent.get('name') or 'Unknown'}"
                )

    if include_library:
        library_agents = await get_library_agents_for_generation(
            user_id=user_id,
            search_query=search_query,
            exclude_graph_id=exclude_graph_id,
            max_results=max_library_results,
        )
        for agent in library_agents:
            graph_id = agent.get("graph_id")
            if graph_id and graph_id not in seen_graph_ids:
                agents.append(agent)
                seen_graph_ids.add(graph_id)

    if include_marketplace and search_query:
        marketplace_agents = await search_marketplace_agents_for_generation(
            search_query=search_query,
            max_results=max_marketplace_results,
        )
        for agent in marketplace_agents:
            graph_id = agent.get("graph_id")
            if graph_id and graph_id not in seen_graph_ids:
                agents.append(agent)
                seen_graph_ids.add(graph_id)

    return agents