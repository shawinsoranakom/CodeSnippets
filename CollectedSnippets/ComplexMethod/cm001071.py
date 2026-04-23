async def get_library_agent_by_id(
    user_id: str, agent_id: str
) -> LibraryAgentSummary | None:
    """Fetch a specific library agent by its ID (library agent ID or graph_id).

    This function tries multiple lookup strategies:
    1. First tries to find by graph_id (AgentGraph primary key)
    2. If not found, tries to find by library agent ID (LibraryAgent primary key)

    This handles both cases:
    - User provides graph_id (e.g., from AgentExecutorBlock)
    - User provides library agent ID (e.g., from library URL)

    Args:
        user_id: The user ID
        agent_id: The ID to look up (can be graph_id or library agent ID)

    Returns:
        LibraryAgentSummary if found, None otherwise
    """
    db = library_db()
    try:
        agent = await db.get_library_agent_by_graph_id(user_id, agent_id)
        if agent:
            logger.debug(f"Found library agent by graph_id: {agent.name}")
            return LibraryAgentSummary(
                graph_id=agent.graph_id,
                graph_version=agent.graph_version,
                name=agent.name,
                description=agent.description,
                input_schema=agent.input_schema,
                output_schema=agent.output_schema,
            )
    except DatabaseError:
        raise
    except Exception as e:
        logger.debug(f"Could not fetch library agent by graph_id {agent_id}: {e}")

    try:
        agent = await db.get_library_agent(agent_id, user_id)
        if agent:
            logger.debug(f"Found library agent by library_id: {agent.name}")
            return LibraryAgentSummary(
                graph_id=agent.graph_id,
                graph_version=agent.graph_version,
                name=agent.name,
                description=agent.description,
                input_schema=agent.input_schema,
                output_schema=agent.output_schema,
            )
    except NotFoundError:
        logger.debug(f"Library agent not found by library_id: {agent_id}")
    except DatabaseError:
        raise
    except Exception as e:
        logger.warning(
            f"Could not fetch library agent by library_id {agent_id}: {e}",
            exc_info=True,
        )

    return None