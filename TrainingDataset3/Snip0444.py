async def create_preset_from_graph_execution(
    user_id: str,
    create_request: library_model.LibraryAgentPresetCreatableFromGraphExecution,
) -> library_model.LibraryAgentPreset:
    """
    Creates a new AgentPreset from an AgentGraphExecution.

    Params:
        user_id: The ID of the user creating the preset.
        create_request: The data used for creation.

    Returns:
        The newly created LibraryAgentPreset.

    Raises:
        DatabaseError: If there's a database error in creating the preset.
    """
    graph_exec_id = create_request.graph_execution_id
    graph_execution = await get_graph_execution(user_id, graph_exec_id)
    if not graph_execution:
        raise NotFoundError(f"Graph execution #{graph_exec_id} not found")

    # Sanity check: credential inputs must be available if required for this preset
    if graph_execution.credential_inputs is None:
        graph = await graph_db.get_graph(
            graph_id=graph_execution.graph_id,
            version=graph_execution.graph_version,
            user_id=graph_execution.user_id,
            include_subgraphs=True,
        )
        if not graph:
            raise NotFoundError(
                f"Graph #{graph_execution.graph_id} not found or accessible"
            )
        elif len(graph.aggregate_credentials_inputs()) > 0:
            raise ValueError(
                f"Graph execution #{graph_exec_id} can't be turned into a preset "
                "because it was run before this feature existed "
                "and so the input credentials were not saved."
            )

    logger.debug(
        f"Creating preset for user #{user_id} from graph execution #{graph_exec_id}",
    )
    return await create_preset(
        user_id=user_id,
        preset=library_model.LibraryAgentPresetCreatable(
            inputs=graph_execution.inputs,
            credentials=graph_execution.credential_inputs or {},
            graph_id=graph_execution.graph_id,
            graph_version=graph_execution.graph_version,
            name=create_request.name,
            description=create_request.description,
            is_active=create_request.is_active,
        ),
    )
