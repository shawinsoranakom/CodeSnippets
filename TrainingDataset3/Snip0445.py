async def update_preset(
    user_id: str,
    preset_id: str,
    inputs: Optional[BlockInput] = None,
    credentials: Optional[dict[str, CredentialsMetaInput]] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> library_model.LibraryAgentPreset:
    """
    Updates an existing AgentPreset for a user.

    Args:
        user_id: The ID of the user updating the preset.
        preset_id: The ID of the preset to update.
        inputs: New inputs object to set on the preset.
        credentials: New credentials to set on the preset.
        name: New name for the preset.
        description: New description for the preset.
        is_active: New active status for the preset.

    Returns:
        The updated LibraryAgentPreset.

    Raises:
        DatabaseError: If there's a database error in updating the preset.
        NotFoundError: If attempting to update a non-existent preset.
    """
    current = await get_preset(user_id, preset_id)  # assert ownership
    if not current:
        raise NotFoundError(f"Preset #{preset_id} not found for user #{user_id}")
    logger.debug(
        f"Updating preset #{preset_id} ({repr(current.name)}) for user #{user_id}",
    )
    try:
        async with transaction() as tx:
            update_data: prisma.types.AgentPresetUpdateInput = {}
            if name:
                update_data["name"] = name
            if description:
                update_data["description"] = description
            if is_active is not None:
                update_data["isActive"] = is_active
            if inputs or credentials:
                if not (inputs and credentials):
                    raise ValueError(
                        "Preset inputs and credentials must be provided together"
                    )
                update_data["InputPresets"] = {
                    "create": [
                        prisma.types.AgentNodeExecutionInputOutputCreateWithoutRelationsInput(  # noqa
                            name=name, data=SafeJson(data)
                        )
                        for name, data in {
                            **inputs,
                            **{
                                key: creds_meta.model_dump(exclude_none=True)
                                for key, creds_meta in credentials.items()
                            },
                        }.items()
                    ],
                }
                # Existing InputPresets must be deleted, in a separate query
                await prisma.models.AgentNodeExecutionInputOutput.prisma(
                    tx
                ).delete_many(where={"agentPresetId": preset_id})

            updated = await prisma.models.AgentPreset.prisma(tx).update(
                where={"id": preset_id},
                data=update_data,
                include=AGENT_PRESET_INCLUDE,
            )
        if not updated:
            raise RuntimeError(f"AgentPreset #{preset_id} vanished while updating")
        return library_model.LibraryAgentPreset.from_db(updated)
    except prisma.errors.PrismaError as e:
        logger.error(f"Database error updating preset: {e}")
        raise DatabaseError("Failed to update preset") from e
