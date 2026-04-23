async def update_graph(
    graph_id: str,
    graph: graph_db.Graph,
    user_id: Annotated[str, Security(get_user_id)],
) -> graph_db.GraphModel:
    if graph.id and graph.id != graph_id:
        raise HTTPException(400, detail="Graph ID does not match ID in URI")

    existing_versions = await graph_db.get_graph_all_versions(graph_id, user_id=user_id)
    if not existing_versions:
        raise HTTPException(404, detail=f"Graph #{graph_id} not found")

    graph.version = max(g.version for g in existing_versions) + 1
    current_active_version = next((v for v in existing_versions if v.is_active), None)

    graph = graph_db.make_graph_model(graph, user_id)
    graph.reassign_ids(user_id=user_id, reassign_graph_id=False)
    graph.validate_graph(for_run=False)

    new_graph_version = await graph_db.create_graph(graph, user_id=user_id)

    if new_graph_version.is_active:
        await library_db.update_library_agent_version_and_settings(
            user_id, new_graph_version
        )
        new_graph_version = await on_graph_activate(new_graph_version, user_id=user_id)
        await graph_db.set_graph_active_version(
            graph_id=graph_id, version=new_graph_version.version, user_id=user_id
        )
        if current_active_version:
            await on_graph_deactivate(current_active_version, user_id=user_id)

    new_graph_version_with_subgraphs = await graph_db.get_graph(
        graph_id,
        new_graph_version.version,
        user_id=user_id,
        include_subgraphs=True,
    )
    assert new_graph_version_with_subgraphs
    return new_graph_version_with_subgraphs