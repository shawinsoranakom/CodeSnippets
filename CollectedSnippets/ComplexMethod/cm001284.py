def test_list_files_returns_all_when_no_session(mock_manager_cls, mock_get_workspace):
    mock_get_workspace.return_value = _make_workspace()
    files = [
        _make_file(id="f1", name="a.txt", metadata={"origin": "user-upload"}),
        _make_file(id="f2", name="b.csv", metadata={"origin": "agent-created"}),
    ]
    mock_instance = AsyncMock()
    mock_instance.list_files.return_value = files
    mock_manager_cls.return_value = mock_instance

    response = client.get("/files")
    assert response.status_code == 200

    data = response.json()
    assert len(data["files"]) == 2
    assert data["has_more"] is False
    assert data["offset"] == 0
    assert data["files"][0]["id"] == "f1"
    assert data["files"][0]["metadata"] == {"origin": "user-upload"}
    assert data["files"][1]["id"] == "f2"
    mock_instance.list_files.assert_called_once_with(
        limit=201, offset=0, include_all_sessions=True
    )