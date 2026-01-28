async def update_preset(
    preset_id: str,
    preset: models.LibraryAgentPresetUpdatable,
    user_id: str = Security(autogpt_auth_lib.get_user_id),
) -> models.LibraryAgentPreset:
    """
    Update an existing library agent preset.

    Args:
        preset_id (str): ID of the preset to update.
        preset (models.LibraryAgentPresetUpdatable): The preset data to update.
        user_id (str): ID of the authenticated user.

    Returns:
        models.LibraryAgentPreset: The updated preset.

    Raises:
        HTTPException: If an error occurs while updating the preset.
    """
    current = await get_preset(preset_id, user_id=user_id)
    if not current:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"Preset #{preset_id} not found")

    graph = await get_graph(
        current.graph_id,
        current.graph_version,
        user_id=user_id,
    )
    if not graph:
        raise HTTPException(
            status.HTTP_410_GONE,
            f"Graph #{current.graph_id} not accessible (anymore)",
        )

    trigger_inputs_updated, new_webhook, feedback = False, None, None
    if (trigger_node := graph.webhook_input_node) and (
        preset.inputs is not None and preset.credentials is not None
    ):
        trigger_config_with_credentials = {
            **preset.inputs,
            **(
                make_node_credentials_input_map(graph, preset.credentials).get(
                    trigger_node.id
                )
                or {}
            ),
        }
        new_webhook, feedback = await setup_webhook_for_block(
            user_id=user_id,
            trigger_block=graph.webhook_input_node.block,
            trigger_config=trigger_config_with_credentials,
            for_preset_id=preset_id,
        )
        trigger_inputs_updated = True
        if not new_webhook:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Could not update trigger configuration: {feedback}",
            )

    try:
        updated = await db.update_preset(
            user_id=user_id,
            preset_id=preset_id,
            inputs=preset.inputs,
            credentials=preset.credentials,
            name=preset.name,
            description=preset.description,
            is_active=preset.is_active,
        )
    except Exception as e:
        logger.exception("Preset update failed for user %s: %s", user_id, e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e)
        )

    # Update the webhook as well, if necessary
    if trigger_inputs_updated:
        updated = await db.set_preset_webhook(
            user_id, preset_id, new_webhook.id if new_webhook else None
        )

        # Clean up webhook if it is now unused
        if current.webhook_id and (
            current.webhook_id != (new_webhook.id if new_webhook else None)
        ):
            current_webhook = await get_webhook(current.webhook_id)
            credentials = (
                await credentials_manager.get(user_id, current_webhook.credentials_id)
                if current_webhook.credentials_id
                else None
            )
            await get_webhook_manager(
                current_webhook.provider
            ).prune_webhook_if_dangling(user_id, current_webhook.id, credentials)

    return updated
