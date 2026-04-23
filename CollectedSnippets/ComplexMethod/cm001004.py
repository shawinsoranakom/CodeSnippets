async def test_read_workspace_file_with_offset_and_length(setup_test_data):
    """Read a slice of a text file using offset and length."""
    user = setup_test_data["user"]
    session = make_session(user.id)

    # Write a known-content file
    content = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" * 100  # 2600 chars
    write_tool = WriteWorkspaceFileTool()
    write_resp = await write_tool._execute(
        user_id=user.id,
        session=session,
        filename="ranged_test.txt",
        content=content,
    )
    assert isinstance(write_resp, WorkspaceWriteResponse), write_resp.message
    file_id = write_resp.file_id

    from backend.copilot.tools.workspace_files import WorkspaceFileContentResponse

    read_tool = ReadWorkspaceFileTool()

    # Read with offset=100, length=50
    resp = await read_tool._execute(
        user_id=user.id, session=session, file_id=file_id, offset=100, length=50
    )
    assert isinstance(resp, WorkspaceFileContentResponse), resp.message
    decoded = base64.b64decode(resp.content_base64).decode()
    assert decoded == content[100:150]
    assert "100" in resp.message
    assert "2,600" in resp.message  # total chars (comma-formatted)

    # Read with offset only (no length) — returns from offset to end
    resp2 = await read_tool._execute(
        user_id=user.id, session=session, file_id=file_id, offset=2500
    )
    assert isinstance(resp2, WorkspaceFileContentResponse)
    decoded2 = base64.b64decode(resp2.content_base64).decode()
    assert decoded2 == content[2500:]
    assert len(decoded2) == 100

    # Read with offset beyond file length — returns empty string
    resp3 = await read_tool._execute(
        user_id=user.id, session=session, file_id=file_id, offset=9999, length=10
    )
    assert isinstance(resp3, WorkspaceFileContentResponse)
    decoded3 = base64.b64decode(resp3.content_base64).decode()
    assert decoded3 == ""

    # Cleanup
    delete_tool = DeleteWorkspaceFileTool()
    await delete_tool._execute(user_id=user.id, session=session, file_id=file_id)