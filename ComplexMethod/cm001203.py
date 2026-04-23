async def get_library_agent(id: str, user_id: str) -> library_model.LibraryAgent:
    """
    Get a specific agent from the user's library.

    Args:
        id: ID of the library agent to retrieve.
        user_id: ID of the authenticated user.

    Returns:
        The requested LibraryAgent.

    Raises:
        NotFoundError: If the specified agent does not exist.
        DatabaseError: If there's an error during retrieval.
    """
    library_agent = await prisma.models.LibraryAgent.prisma().find_first(
        where={
            "id": id,
            "userId": user_id,
            "isDeleted": False,
        },
        include=library_agent_include(user_id),
    )

    if not library_agent:
        raise NotFoundError(f"Library agent #{id} not found")

    # Fetch marketplace listing if the agent has been published
    store_listing = None
    profile = None
    if library_agent.AgentGraph:
        store_listing = await prisma.models.StoreListing.prisma().find_first(
            where={
                "agentGraphId": library_agent.AgentGraph.id,
                "isDeleted": False,
                "hasApprovedVersion": True,
            },
            include={
                "ActiveVersion": True,
            },
        )
        if store_listing and store_listing.ActiveVersion and store_listing.owningUserId:
            # Fetch Profile separately since User doesn't have a direct Profile relation
            profile = await prisma.models.Profile.prisma().find_first(
                where={"userId": store_listing.owningUserId}
            )

    schedule_info = (
        await _fetch_schedule_info(user_id, graph_id=library_agent.AgentGraph.id)
        if library_agent.AgentGraph
        else {}
    )

    return library_model.LibraryAgent.from_db(
        library_agent,
        sub_graphs=(
            await graph_db.get_sub_graphs(library_agent.AgentGraph)
            if library_agent.AgentGraph
            else None
        ),
        store_listing=store_listing,
        profile=profile,
        schedule_info=schedule_info,
    )