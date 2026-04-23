async def validate_graph_execution_permissions(
    user_id: str, graph_id: str, graph_version: int, is_sub_graph: bool = False
) -> None:
    """
    Validate that a user has permission to execute a specific graph.

    This function performs comprehensive authorization checks and raises specific
    exceptions for different types of failures to enable appropriate error handling.

    ## Logic
    A user can execute a graph if any of these is true:
    1. They own the graph and some version of it is still listed in their library
    2. The graph is in the user's library (non-deleted, non-archived)
    3. The graph is published in the marketplace and listed in their library
    4. The graph is published in the marketplace and is being executed as a sub-agent

    Args:
        graph_id: The ID of the graph to check
        user_id: The ID of the user
        graph_version: The version of the graph to check
        is_sub_graph: Whether this is being executed as a sub-graph.
            If `True`, the graph isn't required to be in the user's Library.

    Raises:
        GraphNotAccessibleError: If the graph is not accessible to the user.
        GraphNotInLibraryError: If the graph is not in the user's library (deleted/archived).
        NotAuthorizedError: If the user lacks execution permissions for other reasons
    """
    graph, library_agent = await asyncio.gather(
        AgentGraph.prisma().find_unique(
            where={"graphVersionId": {"id": graph_id, "version": graph_version}}
        ),
        LibraryAgent.prisma().find_first(
            where={
                "userId": user_id,
                "agentGraphId": graph_id,
                "agentGraphVersion": graph_version,
                "isDeleted": False,
                "isArchived": False,
            }
        ),
    )

    # Step 1: Check if user owns this graph
    user_owns_graph = graph and graph.userId == user_id

    # Step 2: Check if the exact graph version is in the library.
    user_has_in_library = library_agent is not None
    owner_has_live_library_entry = user_has_in_library
    if user_owns_graph and not user_has_in_library:
        # Owners are allowed to execute a new version as long as some live
        # library entry still exists for the graph. Non-owners stay
        # version-specific.
        owner_has_live_library_entry = (
            await LibraryAgent.prisma().find_first(
                where={
                    "userId": user_id,
                    "agentGraphId": graph_id,
                    "isDeleted": False,
                    "isArchived": False,
                }
            )
            is not None
        )

    # Step 3: Apply permission logic
    # Access is granted if the user owns it, it's in the marketplace, OR
    # it's in the user's library ("you added it, you keep it").
    if not (
        user_owns_graph
        or user_has_in_library
        or await is_graph_published_in_marketplace(graph_id, graph_version)
    ):
        raise GraphNotAccessibleError(
            f"You do not have access to graph #{graph_id} v{graph_version}: "
            "it is not owned by you, not in your library, "
            "and not available in the Marketplace"
        )
    elif not (user_has_in_library or owner_has_live_library_entry or is_sub_graph):
        raise GraphNotInLibraryError(f"Graph #{graph_id} is not in your library")