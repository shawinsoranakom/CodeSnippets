async def search_marketplace_agents_for_generation(
    search_query: str,
    max_results: int = 10,
) -> list[LibraryAgentSummary]:
    """Search marketplace agents formatted for Agent Generator.

    Fetches marketplace agents and their full schemas so they can be used
    as sub-agents in generated workflows.

    Args:
        search_query: Search term to find relevant public agents
        max_results: Maximum number of agents to return (default 10)

    Returns:
        List of LibraryAgentSummary with full input/output schemas
    """
    search_term = search_query.strip()
    if len(search_term) > 100:
        raise ValueError(
            f"Search query is too long ({len(search_term)} chars, max 100). "
            f"Please use a shorter, more specific search term."
        )

    try:
        response = await store_db().get_store_agents(
            search_query=search_term,
            page=1,
            page_size=max_results,
        )

        agents_with_graphs = [
            agent for agent in response.agents if agent.agent_graph_id
        ]

        if not agents_with_graphs:
            return []

        graph_ids = [agent.agent_graph_id for agent in agents_with_graphs]
        graphs = await graph_db().get_store_listed_graphs(graph_ids)

        results: list[LibraryAgentSummary] = []
        for agent in agents_with_graphs:
            graph_id = agent.agent_graph_id
            if graph_id and graph_id in graphs:
                graph = graphs[graph_id]
                results.append(
                    LibraryAgentSummary(
                        graph_id=graph.id,
                        graph_version=graph.version,
                        name=agent.agent_name,
                        description=agent.description,
                        input_schema=graph.input_schema,
                        output_schema=graph.output_schema,
                    )
                )
        return results
    except Exception as e:
        logger.warning(f"Failed to search marketplace agents: {e}")
        return []