async def _search_marketplace(query: str, session_id: str | None) -> ToolResponseBase:
    """Search marketplace agents, with direct creator/slug lookup fallback."""
    query = query.strip()
    if not query:
        return ErrorResponse(
            message="Please provide a search query", session_id=session_id
        )

    agents: list[AgentInfo] = []
    try:
        # Direct lookup if query matches "creator/slug" pattern
        if is_creator_slug(query):
            logger.info(f"Query looks like creator/slug, trying direct lookup: {query}")
            creator, slug = query.split("/", 1)
            agent_info = await _get_marketplace_agent_by_slug(creator, slug)
            if agent_info:
                agents.append(agent_info)

        if not agents:
            logger.info(f"Searching marketplace for: {query}")
            results = await store_db().get_store_agents(search_query=query, page_size=5)
            for agent in results.agents:
                agents.append(_marketplace_agent_to_info(agent))
    except NotFoundError:
        pass
    except DatabaseError as e:
        logger.error(f"Error searching marketplace: {e}", exc_info=True)
        return ErrorResponse(
            message="Failed to search marketplace. Please try again.",
            error=str(e),
            session_id=session_id,
        )

    if not agents:
        return NoResultsResponse(
            message=(
                f"No agents found matching '{query}'. Let the user know they can "
                "try different keywords or browse the marketplace. Also let them "
                "know you can create a custom agent for them based on their needs."
            ),
            suggestions=[
                "Try more general terms",
                "Browse categories in the marketplace",
                "Check spelling",
            ],
            session_id=session_id,
        )

    return AgentsFoundResponse(
        message=(
            "Now you have found some options for the user to choose from. "
            "You can add a link to a recommended agent at: /marketplace/agent/agent_id "
            "Please ask the user if they would like to use any of these agents. "
            "Let the user know we can create a custom agent for them based on their needs."
        ),
        title=f"Found {len(agents)} agent{'s' if len(agents) != 1 else ''} for '{query}'",
        agents=agents,
        count=len(agents),
        session_id=session_id,
    )