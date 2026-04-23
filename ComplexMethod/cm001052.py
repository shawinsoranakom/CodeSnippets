async def _get_library_agent_by_id(user_id: str, agent_id: str) -> AgentInfo | None:
    """Fetch a library agent by ID (library agent ID or graph_id).

    Tries multiple lookup strategies:
    1. First by graph_id (AgentGraph primary key)
    2. Then by library agent ID (LibraryAgent primary key)
    """
    lib_db = library_db()

    try:
        agent = await lib_db.get_library_agent_by_graph_id(user_id, agent_id)
        if agent:
            return _library_agent_to_info(agent)
    except NotFoundError:
        pass
    except DatabaseError:
        raise
    except Exception as e:
        logger.warning(
            f"Could not fetch library agent by graph_id {agent_id}: {e}",
            exc_info=True,
        )

    try:
        agent = await lib_db.get_library_agent(agent_id, user_id)
        if agent:
            return _library_agent_to_info(agent)
    except NotFoundError:
        pass
    except DatabaseError:
        raise
    except Exception as e:
        logger.warning(
            f"Could not fetch library agent by library_id {agent_id}: {e}",
            exc_info=True,
        )

    return None