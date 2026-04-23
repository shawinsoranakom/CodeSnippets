async def get_or_create_default_folder(session: AsyncSession, user_id: UUID) -> FolderRead:
    """Ensure the default folder exists for the given user_id. If it doesn't exist, create it.

    Uses an idempotent insertion approach to handle concurrent creation gracefully.

    If the DEFAULT_FOLDER_NAME env var is set to a custom value (e.g., "OpenRAG"), this function
    will check for legacy folder names and migrate them to avoid duplicates.

    This implementation avoids an external distributed lock and works with both SQLite and PostgreSQL.

    Args:
        session (AsyncSession): The active database session.
        user_id (UUID): The ID of the user who owns the folder.

    Returns:
        FolderRead: The default folder for the user.
    """
    # First, check if the current default folder exists
    stmt = select(Folder).where(Folder.user_id == user_id, Folder.name == DEFAULT_FOLDER_NAME)
    result = await session.exec(stmt)
    folder = result.first()
    if folder:
        return FolderRead.model_validate(folder, from_attributes=True)

    # Check if a legacy folder exists and migrate it if the name is different from default
    if DEFAULT_FOLDER_NAME not in LEGACY_FOLDER_NAMES:
        for legacy_name in LEGACY_FOLDER_NAMES:
            if legacy_name == DEFAULT_FOLDER_NAME:
                continue  # Skip if legacy name is the same as current default

            legacy_stmt = select(Folder).where(Folder.user_id == user_id, Folder.name == legacy_name)
            legacy_result = await session.exec(legacy_stmt)
            legacy_folder = legacy_result.first()

            if legacy_folder:
                # Migrate the legacy folder by renaming it
                await logger.ainfo(
                    f"Migrating legacy folder '{legacy_name}' to '{DEFAULT_FOLDER_NAME}' for user {user_id}"
                )
                legacy_folder.name = DEFAULT_FOLDER_NAME
                legacy_folder.description = DEFAULT_FOLDER_DESCRIPTION
                session.add(legacy_folder)
                try:
                    await session.flush()
                    await session.refresh(legacy_folder)
                    return FolderRead.model_validate(legacy_folder, from_attributes=True)
                except sa.exc.IntegrityError:
                    # If there's a conflict, rollback and proceed to create new folder
                    await session.rollback()
                    break

    # If no existing folder found, create a new one
    try:
        folder_obj = Folder(user_id=user_id, name=DEFAULT_FOLDER_NAME, description=DEFAULT_FOLDER_DESCRIPTION)
        session.add(folder_obj)
        await session.flush()
        await session.refresh(folder_obj)
    except sa.exc.IntegrityError as e:
        # Another worker may have created the folder concurrently.
        await session.rollback()
        result = await session.exec(stmt)
        folder = result.first()
        if folder:
            return FolderRead.model_validate(folder, from_attributes=True)
        msg = "Failed to get or create default folder"
        raise ValueError(msg) from e
    return FolderRead.model_validate(folder_obj, from_attributes=True)