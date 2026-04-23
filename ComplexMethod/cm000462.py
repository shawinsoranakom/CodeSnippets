async def get_graph(
    graph_id: str,
    version: int | None,
    user_id: str | None,
    *,
    for_export: bool = False,
    include_subgraphs: bool = False,
    skip_access_check: bool = False,
) -> GraphModel | None:
    """
    Retrieves a graph from the DB.
    Defaults to the version with `is_active` if `version` is not passed.

    See also: `get_graph_as_admin()` which bypasses ownership and marketplace
    checks for admin-only routes.

    Returns `None` if the record is not found.
    """
    graph = None

    # Only search graph directly on owned graph (or access check is skipped)
    if skip_access_check or user_id is not None:
        graph_where_clause: AgentGraphWhereInput = {
            "id": graph_id,
        }
        if version is not None:
            graph_where_clause["version"] = version
        if not skip_access_check and user_id is not None:
            graph_where_clause["userId"] = user_id

        graph = await AgentGraph.prisma().find_first(
            where=graph_where_clause,
            include=AGENT_GRAPH_INCLUDE,
            order={"version": "desc"},
        )

    # Use store listed graph to find not owned graph
    if graph is None:
        store_where_clause: StoreListingVersionWhereInput = {
            "agentGraphId": graph_id,
            "submissionStatus": SubmissionStatus.APPROVED,
            "isDeleted": False,
        }
        if version is not None:
            store_where_clause["agentGraphVersion"] = version

        if store_listing := await StoreListingVersion.prisma().find_first(
            where=store_where_clause,
            order={"agentGraphVersion": "desc"},
            include={"AgentGraph": {"include": AGENT_GRAPH_INCLUDE}},
        ):
            graph = store_listing.AgentGraph

    # Fall back to library membership: if the user has the agent in their
    # library (non-deleted, non-archived), grant access even if the agent is
    # no longer published. "You added it, you keep it."
    if graph is None and user_id is not None:
        library_where: dict[str, object] = {
            "userId": user_id,
            "agentGraphId": graph_id,
            "isDeleted": False,
            "isArchived": False,
        }
        if version is not None:
            library_where["agentGraphVersion"] = version

        library_agent = await LibraryAgent.prisma().find_first(
            where=library_where,
            include={"AgentGraph": {"include": AGENT_GRAPH_INCLUDE}},
            order={"agentGraphVersion": "desc"},
        )
        if library_agent and library_agent.AgentGraph:
            graph = library_agent.AgentGraph

    if graph is None:
        return None

    if include_subgraphs or for_export:
        sub_graphs = await get_sub_graphs(graph)
        return GraphModel.from_db(
            graph=graph,
            sub_graphs=sub_graphs,
            for_export=for_export,
        )

    return GraphModel.from_db(graph, for_export)