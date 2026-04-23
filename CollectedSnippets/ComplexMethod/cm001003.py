async def test_workspace_file_round_trip(setup_test_data):
    """E2E: write a file, list it, read it back (with save_to_path), then delete it."""
    user = setup_test_data["user"]
    session = make_session(user.id)
    session_id = session.session_id

    # ---- Write ----
    write_tool = WriteWorkspaceFileTool()
    write_resp = await write_tool._execute(
        user_id=user.id,
        session=session,
        filename="test_round_trip.txt",
        content="Hello from e2e test!",
    )
    assert isinstance(write_resp, WorkspaceWriteResponse), write_resp.message
    file_id = write_resp.file_id

    # ---- List ----
    list_tool = ListWorkspaceFilesTool()
    list_resp = await list_tool._execute(user_id=user.id, session=session)
    assert isinstance(list_resp, WorkspaceFileListResponse), list_resp.message
    assert any(f.file_id == file_id for f in list_resp.files)

    # ---- Read (inline) ----
    read_tool = ReadWorkspaceFileTool()
    read_resp = await read_tool._execute(
        user_id=user.id, session=session, file_id=file_id
    )
    from backend.copilot.tools.workspace_files import WorkspaceFileContentResponse

    assert isinstance(read_resp, WorkspaceFileContentResponse), read_resp.message
    decoded = base64.b64decode(read_resp.content_base64).decode()
    assert decoded == "Hello from e2e test!"

    # ---- Read with save_to_path ----
    from backend.copilot.tools.sandbox import make_session_path

    ephemeral_dir = make_session_path(session_id)
    os.makedirs(ephemeral_dir, exist_ok=True)
    save_path = os.path.join(ephemeral_dir, "saved_copy.txt")

    read_resp2 = await read_tool._execute(
        user_id=user.id, session=session, file_id=file_id, save_to_path=save_path
    )
    assert not isinstance(read_resp2, type(None))
    assert os.path.exists(save_path)
    with open(save_path) as f:
        assert f.read() == "Hello from e2e test!"

    # ---- Delete ----
    delete_tool = DeleteWorkspaceFileTool()
    del_resp = await delete_tool._execute(
        user_id=user.id, session=session, file_id=file_id
    )
    assert isinstance(del_resp, WorkspaceDeleteResponse), del_resp.message
    assert del_resp.success is True

    # Verify file is gone
    list_resp2 = await list_tool._execute(user_id=user.id, session=session)
    assert isinstance(list_resp2, WorkspaceFileListResponse)
    assert not any(f.file_id == file_id for f in list_resp2.files)