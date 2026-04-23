async def update_library_agent(
    library_agent_id: str,
    user_id: str,
    auto_update_version: Optional[bool] = None,
    graph_version: Optional[int] = None,
    is_favorite: Optional[bool] = None,
    is_archived: Optional[bool] = None,
    is_deleted: Optional[Literal[False]] = None,
    settings: Optional[GraphSettings] = None,
    folder_id: Optional[str] = None,
) -> library_model.LibraryAgent:
    """
    Updates the specified LibraryAgent record.

    Args:
        library_agent_id: The ID of the LibraryAgent to update.
        user_id: The owner of this LibraryAgent.
        auto_update_version: Whether the agent should auto-update to active version.
        graph_version: Specific graph version to update to.
        is_favorite: Whether this agent is marked as a favorite.
        is_archived: Whether this agent is archived.
        settings: User-specific settings for this library agent.
        folder_id: Folder ID to move agent to (None to skip).

    Returns:
        The updated LibraryAgent.

    Raises:
        NotFoundError: If the specified LibraryAgent does not exist.
        DatabaseError: If there's an error in the update operation.
    """
    logger.debug(
        f"Updating library agent {library_agent_id} for user {user_id} with "
        f"auto_update_version={auto_update_version}, graph_version={graph_version}, "
        f"is_favorite={is_favorite}, is_archived={is_archived}, settings={settings}"
    )
    update_fields: prisma.types.LibraryAgentUpdateManyMutationInput = {}
    if auto_update_version is not None:
        update_fields["useGraphIsActiveVersion"] = auto_update_version
    if is_favorite is not None:
        update_fields["isFavorite"] = is_favorite
    if is_archived is not None:
        update_fields["isArchived"] = is_archived
    if is_deleted is not None:
        if is_deleted is True:
            raise RuntimeError(
                "Use delete_library_agent() to (soft-)delete library agents"
            )
        update_fields["isDeleted"] = is_deleted
    if settings is not None:
        existing_agent = await get_library_agent(id=library_agent_id, user_id=user_id)
        current_settings_dict = (
            existing_agent.settings.model_dump() if existing_agent.settings else {}
        )
        new_settings = settings.model_dump(exclude_unset=True)
        merged_settings = {**current_settings_dict, **new_settings}
        update_fields["settings"] = SafeJson(merged_settings)
    if folder_id is not None:
        # Authorization: FK only checks existence, not ownership.
        # Verify the folder belongs to this user to prevent cross-user nesting.
        await get_folder(folder_id, user_id)
        update_fields["folderId"] = folder_id

    # If graph_version is provided, update to that specific version
    if graph_version is not None:
        # Apply any other field updates first so they aren't lost
        if update_fields:
            await prisma.models.LibraryAgent.prisma().update_many(
                where={"id": library_agent_id, "userId": user_id},
                data=update_fields,
            )
        # Get the current agent to find its graph_id
        agent = await get_library_agent(id=library_agent_id, user_id=user_id)
        # Update to the specified version using existing function
        return await update_agent_version_in_library(
            user_id=user_id,
            agent_graph_id=agent.graph_id,
            agent_graph_version=graph_version,
        )

    # Otherwise, just update the simple fields
    if not update_fields:
        raise ValueError("No values were passed to update")

    n_updated = await prisma.models.LibraryAgent.prisma().update_many(
        where={"id": library_agent_id, "userId": user_id},
        data=update_fields,
    )
    if n_updated < 1:
        raise NotFoundError(f"Library agent {library_agent_id} not found")

    return await get_library_agent(
        id=library_agent_id,
        user_id=user_id,
    )