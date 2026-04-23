async def update_graph_in_library(
    graph: graph_db.Graph,
    user_id: str,
) -> tuple[graph_db.GraphModel, library_model.LibraryAgent]:
    """Create a new version of an existing graph and update the library entry."""
    existing_versions = await graph_db.get_graph_all_versions(graph.id, user_id)
    current_active_version = (
        next((v for v in existing_versions if v.is_active), None)
        if existing_versions
        else None
    )
    graph.version = (
        max(v.version for v in existing_versions) + 1 if existing_versions else 1
    )

    graph_model = graph_db.make_graph_model(graph, user_id)
    graph_model.reassign_ids(user_id=user_id, reassign_graph_id=False)

    created_graph = await graph_db.create_graph(graph_model, user_id)

    library_agent = await get_library_agent_by_graph_id(
        user_id, created_graph.id, include_archived=True
    )
    if not library_agent:
        raise NotFoundError(f"Library agent not found for graph {created_graph.id}")

    library_agent = await update_library_agent_version_and_settings(
        user_id, created_graph
    )

    if created_graph.is_active:
        created_graph = await on_graph_activate(created_graph, user_id=user_id)
        await graph_db.set_graph_active_version(
            graph_id=created_graph.id,
            version=created_graph.version,
            user_id=user_id,
        )
        if current_active_version:
            await on_graph_deactivate(current_active_version, user_id=user_id)

    return created_graph, library_agent