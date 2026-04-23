async def test_create_flow_after_all_folders_deleted_creates_default_folder(
    client: AsyncClient, logged_in_headers, active_user
):
    """Test the zero-folder scenario: creating a flow after deleting all folders.

    This is the critical bug fix test. When all folders are deleted, creating a new flow
    should automatically create a default folder instead of creating an orphaned flow.
    """
    # First, delete all folders for this user
    async with session_scope() as session:
        stmt = select(Folder).where(Folder.user_id == active_user.id)
        folders = (await session.exec(stmt)).all()
        for folder in folders:
            await session.delete(folder)
        await session.commit()

    # Verify no folders exist for this user
    async with session_scope() as session:
        stmt = select(Folder).where(Folder.user_id == active_user.id)
        folders = (await session.exec(stmt)).all()
        assert len(folders) == 0, "All folders should be deleted"

    # Now create a flow - this should auto-create a default folder
    flow_data = {
        "name": "Flow Created After All Folders Deleted",
        "data": {},
    }

    response = await client.post("api/v1/flows/", json=flow_data, headers=logged_in_headers)

    assert response.status_code == status.HTTP_201_CREATED
    result = response.json()

    # The flow should NOT be orphaned - it should have a valid folder_id
    assert result["folder_id"] is not None

    # Verify the folder was auto-created and exists
    async with session_scope() as session:
        folder = await session.get(Folder, uuid.UUID(result["folder_id"]))
        assert folder is not None
        assert folder.user_id == active_user.id
        assert folder.name == DEFAULT_FOLDER_NAME