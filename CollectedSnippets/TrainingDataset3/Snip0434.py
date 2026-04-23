async def setup_trigger(
    params: models.TriggeredPresetSetupRequest = Body(),
    user_id: str = Security(autogpt_auth_lib.get_user_id),
) -> models.LibraryAgentPreset:
    """
    Sets up a webhook-triggered `LibraryAgentPreset` for a `LibraryAgent`.
    Returns the correspondingly created `LibraryAgentPreset` with `webhook_id` set.
    """
    graph = await get_graph(
        params.graph_id, version=params.graph_version, user_id=user_id
    )
    if not graph:
        raise HTTPException(
            status.HTTP_410_GONE,
            f"Graph #{params.graph_id} not accessible (anymore)",
        )
    if not (trigger_node := graph.webhook_input_node):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Graph #{params.graph_id} does not have a webhook node",
        )

    trigger_config_with_credentials = {
        **params.trigger_config,
        **(
            make_node_credentials_input_map(graph, params.agent_credentials).get(
                trigger_node.id
            )
            or {}
        ),
    }

    new_webhook, feedback = await setup_webhook_for_block(
        user_id=user_id,
        trigger_block=trigger_node.block,
        trigger_config=trigger_config_with_credentials,
    )
    if not new_webhook:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Could not set up webhook: {feedback}",
        )

    new_preset = await db.create_preset(
        user_id=user_id,
        preset=models.LibraryAgentPresetCreatable(
            graph_id=params.graph_id,
            graph_version=params.graph_version,
            name=params.name,
            description=params.description,
            inputs=trigger_config_with_credentials,
            credentials=params.agent_credentials,
            webhook_id=new_webhook.id,
            is_active=True,
        ),
    )
    return new_preset
