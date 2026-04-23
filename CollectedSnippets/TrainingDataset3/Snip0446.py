async def fork_library_agent(
    library_agent_id: str, user_id: str
) -> library_model.LibraryAgent:
    """
    Clones a library agent and its underyling graph and nodes (with new ids) for the given user.

    Args:
        library_agent_id: The ID of the library agent to fork.
        user_id: The ID of the user who owns the library agent.

    Returns:
        The forked parent (if it has sub-graphs) LibraryAgent.

    Raises:
        DatabaseError: If there's an error during the forking process.
    """
    logger.debug(f"Forking library agent {library_agent_id} for user {user_id}")
    try:
        # Fetch the original agent
        original_agent = await get_library_agent(library_agent_id, user_id)

        # Check if user owns the library agent
        # TODO: once we have open/closed sourced agents this needs to be enabled ~kcze
        # + update library/agents/[id]/page.tsx agent actions
        # if not original_agent.can_access_graph:
        #     raise DatabaseError(
        #         f"User {user_id} cannot access library agent graph {library_agent_id}"
        #     )

        # Fork the underlying graph and nodes
        new_graph = await graph_db.fork_graph(
            original_agent.graph_id, original_agent.graph_version, user_id
        )
        new_graph = await on_graph_activate(new_graph, user_id=user_id)

        # Create a library agent for the new graph, preserving safe mode settings
        return (
            await create_library_agent(
                new_graph,
                user_id,
                hitl_safe_mode=original_agent.settings.human_in_the_loop_safe_mode,
                sensitive_action_safe_mode=original_agent.settings.sensitive_action_safe_mode,
            )
        )[0]
    except prisma.errors.PrismaError as e:
        logger.error(f"Database error cloning library agent: {e}")
        raise DatabaseError("Failed to fork library agent") from e
