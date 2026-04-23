async def update_folder(
    folder_id: str,
    user_id: str,
    name: Optional[str] = None,
    icon: Optional[str] = None,
    color: Optional[str] = None,
) -> library_model.LibraryFolder:
    """
    Updates a folder's properties.

    Args:
        folder_id: The ID of the folder to update.
        user_id: The ID of the user.
        name: New folder name.
        icon: New icon identifier.
        color: New hex color code.

    Returns:
        The updated LibraryFolder.

    Raises:
        NotFoundError: If the folder doesn't exist.
        DatabaseError: If there's a database error.
    """
    logger.debug(f"Updating folder #{folder_id} for user #{user_id}")

    # Authorization: update uses where={"id": ...} without userId,
    # so we must verify ownership first.
    await get_folder(folder_id, user_id)

    update_data: prisma.types.LibraryFolderUpdateInput = {}
    if name is not None:
        update_data["name"] = name
    if icon is not None:
        update_data["icon"] = icon
    if color is not None:
        update_data["color"] = color

    if not update_data:
        return await get_folder(folder_id, user_id)

    try:
        folder = await prisma.models.LibraryFolder.prisma().update(
            where={"id": folder_id},
            data=update_data,
            include=LIBRARY_FOLDER_INCLUDE,
        )
    except prisma.errors.UniqueViolationError:
        raise FolderAlreadyExistsError(
            "A folder with this name already exists in this location"
        )

    if not folder:
        raise NotFoundError(f"Folder #{folder_id} not found")

    return library_model.LibraryFolder.from_db(
        folder,
        agent_count=len(folder.LibraryAgents) if folder.LibraryAgents else 0,
        subfolder_count=len(folder.Children) if folder.Children else 0,
    )