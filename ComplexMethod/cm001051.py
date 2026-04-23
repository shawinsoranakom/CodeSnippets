async def _search_library(
    query: str,
    session_id: str | None,
    user_id: str | None,
    include_graph: bool = False,
) -> ToolResponseBase:
    """Search user's library agents, with direct UUID lookup fallback."""
    if not user_id:
        return ErrorResponse(
            message="User authentication required to search library",
            session_id=session_id,
        )

    query = query.strip()
    # Normalize list-all keywords to empty string
    if query.lower() in _LIST_ALL_KEYWORDS:
        query = ""

    agents: list[AgentInfo] = []
    try:
        if is_uuid(query):
            logger.info(f"Query looks like UUID, trying direct lookup: {query}")
            agent = await _get_library_agent_by_id(user_id, query)
            if agent:
                agents.append(agent)

        if not agents:
            logger.info(
                f"{'Listing all agents in' if not query else 'Searching'} "
                f"user library{'' if not query else f' for: {query}'}"
            )
            results = await library_db().list_library_agents(
                user_id=user_id,
                search_term=query or None,
                page_size=50 if not query else 10,
            )
            for agent in results.agents:
                agents.append(_library_agent_to_info(agent))
    except NotFoundError:
        pass
    except DatabaseError as e:
        logger.error(f"Error searching library: {e}", exc_info=True)
        return ErrorResponse(
            message="Failed to search library. Please try again.",
            error=str(e),
            session_id=session_id,
        )

    truncation_notice: str | None = None
    if include_graph and agents:
        truncation_notice = await _enrich_agents_with_graph(agents, user_id)

    if not agents:
        if not query:
            return NoResultsResponse(
                message=(
                    "Your library is empty. Let the user know they can browse the "
                    "marketplace to find agents, or you can create a custom agent "
                    "for them based on their needs."
                ),
                suggestions=[
                    "Browse the marketplace to find and add agents",
                    "Use find_agent to search the marketplace",
                ],
                session_id=session_id,
            )
        return NoResultsResponse(
            message=(
                f"No agents matching '{query}' found in your library. Let the "
                "user know you can create a custom agent for them based on "
                "their needs."
            ),
            suggestions=[
                "Try different keywords",
                "Use find_agent to search the marketplace",
                "Check your library at /library",
            ],
            session_id=session_id,
        )

    if not query:
        title = f"Found {len(agents)} agent{'s' if len(agents) != 1 else ''} in your library"
    else:
        title = f"Found {len(agents)} agent{'s' if len(agents) != 1 else ''} in your library for '{query}'"

    message = (
        "Found agents in the user's library. You can provide a link to view "
        "an agent at: /library/agents/{agent_id}. Use agent_output to get "
        "execution results, or run_agent to execute. Let the user know we can "
        "create a custom agent for them based on their needs."
    )
    if truncation_notice:
        message = f"{message}\n\nNote: {truncation_notice}"

    return AgentsFoundResponse(
        message=message,
        title=title,
        agents=agents,
        count=len(agents),
        session_id=session_id,
    )