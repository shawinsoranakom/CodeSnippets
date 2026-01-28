async def delete_preset(
    preset_id: str,
    user_id: str = Security(autogpt_auth_lib.get_user_id),
) -> None:
    """
    Delete a preset by its ID. Returns 204 No Content on success.

    Args:
        preset_id (str): ID of the preset to delete.
        user_id (str): ID of the authenticated user.

    Raises:
        HTTPException: If an error occurs while deleting the preset.
    """
    preset = await db.get_preset(user_id, preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset #{preset_id} not found for user #{user_id}",
        )

    # Detach and clean up the attached webhook, if any
    if preset.webhook_id:
        webhook = await get_webhook(preset.webhook_id)
        await db.set_preset_webhook(user_id, preset_id, None)

        # Clean up webhook if it is now unused
        credentials = (
            await credentials_manager.get(user_id, webhook.credentials_id)
            if webhook.credentials_id
            else None
        )
        await get_webhook_manager(webhook.provider).prune_webhook_if_dangling(
            user_id, webhook.id, credentials
        )

    try:
        await db.delete_preset(user_id, preset_id)
    except Exception as e:
        logger.exception(
            "Error deleting preset %s for user %s: %s", preset_id, user_id, e
        )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e),
        )


@router.post(
    "/presets/{preset_id}/execute",
    tags=["presets"],
    summary="Execute a preset",
    description="Execute a preset with the given graph and node input for the current user.",
)
async def execute_preset(
    preset_id: str,
    user_id: str = Security(autogpt_auth_lib.get_user_id),
    inputs: dict[str, Any] = Body(..., embed=True, default_factory=dict),
    credential_inputs: dict[str, CredentialsMetaInput] = Body(
        ..., embed=True, default_factory=dict
    ),
) -> GraphExecutionMeta:
    """
    Execute a preset given graph parameters, returning the execution ID on success.

    Args:
        preset_id: ID of the preset to execute.
        user_id: ID of the authenticated user.
        inputs: Optionally, inputs to override the preset for execution.
        credential_inputs: Optionally, credentials to override the preset for execution.

    Returns:
        GraphExecutionMeta: Object representing the created execution.

    Raises:
        HTTPException: If the preset is not found or an error occurs while executing the preset.
    """
    preset = await db.get_preset(user_id, preset_id)
    if not preset:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Preset #{preset_id} not found",
        )

    # Merge input overrides with preset inputs
    merged_node_input = preset.inputs | inputs
    merged_credential_inputs = preset.credentials | credential_inputs

    return await add_graph_execution(
        user_id=user_id,
        graph_id=preset.graph_id,
        graph_version=preset.graph_version,
        preset_id=preset_id,
        inputs=merged_node_input,
        graph_credentials_inputs=merged_credential_inputs,
    )
