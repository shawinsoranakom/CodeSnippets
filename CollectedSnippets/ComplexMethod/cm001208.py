async def move_folder(
    folder_id: str,
    user_id: str,
    target_parent_id: Optional[str],
) -> library_model.LibraryFolder:
    """
    Moves a folder to a new parent.

    Args:
        folder_id: The ID of the folder to move.
        user_id: The ID of the user.
        target_parent_id: The target parent ID (None for root).

    Returns:
        The moved LibraryFolder.

    Raises:
        FolderValidationError: If the move is invalid.
        NotFoundError: If the folder doesn't exist.
        DatabaseError: If there's a database error.
    """
    logger.debug(f"Moving folder #{folder_id} to parent #{target_parent_id}")

    # Authorization: update uses where={"id": ...} without userId,
    # so we must verify ownership first.
    await get_folder(folder_id, user_id)

    # Authorization: FK only checks existence, not ownership.
    # Verify the target parent belongs to this user to prevent cross-user nesting.
    if target_parent_id:
        await get_folder(target_parent_id, user_id)

    # Validate no circular reference
    if target_parent_id:
        if await _is_descendant_of(target_parent_id, folder_id, user_id):
            raise FolderValidationError("Cannot move folder into its own descendant")

    try:
        folder = await prisma.models.LibraryFolder.prisma().update(
            where={"id": folder_id},
            data={
                "parentId": target_parent_id,
            },
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