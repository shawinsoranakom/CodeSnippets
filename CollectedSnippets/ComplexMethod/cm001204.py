async def create_library_agent(
    graph: graph_db.GraphModel,
    user_id: str,
    hitl_safe_mode: bool = True,
    sensitive_action_safe_mode: bool = False,
    create_library_agents_for_sub_graphs: bool = True,
    folder_id: str | None = None,
) -> list[library_model.LibraryAgent]:
    """
    Adds an agent to the user's library (LibraryAgent table).

    Args:
        agent: The agent/Graph to add to the library.
        user_id: The user to whom the agent will be added.
        hitl_safe_mode: Whether HITL blocks require manual review (default True).
        sensitive_action_safe_mode: Whether sensitive action blocks require review.
        create_library_agents_for_sub_graphs: If True, creates LibraryAgent records for sub-graphs as well.

    Returns:
        The newly created LibraryAgent records.
        If the graph has sub-graphs, the parent graph will always be the first entry in the list.

    Raises:
        NotFoundError: If the specified agent does not exist.
        DatabaseError: If there's an error during creation or if image generation fails.
    """
    logger.info(
        f"Creating library agent for graph #{graph.id} v{graph.version}; user:<redacted>"
    )

    # Authorization: FK only checks existence, not ownership.
    # Verify the folder belongs to this user to prevent cross-user nesting.
    if folder_id:
        await get_folder(folder_id, user_id)

    graph_entries = (
        [graph, *graph.sub_graphs] if create_library_agents_for_sub_graphs else [graph]
    )

    async with transaction() as tx:
        library_agents = await asyncio.gather(
            *(
                prisma.models.LibraryAgent.prisma(tx).upsert(
                    where={
                        "userId_agentGraphId_agentGraphVersion": {
                            "userId": user_id,
                            "agentGraphId": graph_entry.id,
                            "agentGraphVersion": graph_entry.version,
                        }
                    },
                    data={
                        "create": prisma.types.LibraryAgentCreateInput(
                            isCreatedByUser=(user_id == graph.user_id),
                            useGraphIsActiveVersion=True,
                            User={"connect": {"id": user_id}},
                            AgentGraph={
                                "connect": {
                                    "graphVersionId": {
                                        "id": graph_entry.id,
                                        "version": graph_entry.version,
                                    }
                                }
                            },
                            settings=SafeJson(
                                GraphSettings.from_graph(
                                    graph_entry,
                                    hitl_safe_mode=hitl_safe_mode,
                                    sensitive_action_safe_mode=sensitive_action_safe_mode,
                                ).model_dump()
                            ),
                            **(
                                {"Folder": {"connect": {"id": folder_id}}}
                                if folder_id and graph_entry is graph
                                else {}
                            ),
                        ),
                        "update": {
                            "isDeleted": False,
                            "isArchived": False,
                            "useGraphIsActiveVersion": True,
                            "settings": SafeJson(
                                GraphSettings.from_graph(
                                    graph_entry,
                                    hitl_safe_mode=hitl_safe_mode,
                                    sensitive_action_safe_mode=sensitive_action_safe_mode,
                                ).model_dump()
                            ),
                            **(
                                {"Folder": {"connect": {"id": folder_id}}}
                                if folder_id and graph_entry is graph
                                else {}
                            ),
                        },
                    },
                    include=library_agent_include(
                        user_id, include_nodes=False, include_executions=False
                    ),
                )
                for graph_entry in graph_entries
            )
        )

    # Generate images for the main graph and sub-graphs
    for agent, graph in zip(library_agents, graph_entries):
        asyncio.create_task(add_generated_agent_image(graph, user_id, agent.id))

    schedule_info = await _fetch_schedule_info(user_id)
    return [
        library_model.LibraryAgent.from_db(agent, schedule_info=schedule_info)
        for agent in library_agents
    ]