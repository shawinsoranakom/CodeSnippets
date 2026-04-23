def test_move_files_handles_dest_and_storage_move(monkeypatch):
    module = _load_file_api_service(monkeypatch)
    moved = []
    updated = []

    monkeypatch.setattr(
        module.FileService,
        "get_by_id",
        lambda file_id: (False, None) if file_id == "missing" else (True, _DummyFile(file_id, module.FileType.FOLDER.value, name="dest")),
    )
    monkeypatch.setattr(
        module.FileService,
        "get_by_ids",
        lambda _ids: [_DummyFile("file1", module.FileType.DOC.value, parent_id="src", location="old", name="a.txt")],
    )
    monkeypatch.setattr(module.settings, "STORAGE_IMPL", SimpleNamespace(
        obj_exist=lambda *_args, **_kwargs: False,
        put=lambda *_args, **_kwargs: None,
        rm=lambda *_args, **_kwargs: None,
        move=lambda old_bucket, old_loc, new_bucket, new_loc: moved.append((old_bucket, old_loc, new_bucket, new_loc)),
    ))
    monkeypatch.setattr(module.FileService, "update_by_id", lambda file_id, data: updated.append((file_id, data)) or True)

    ok, message = _run(module.move_files("tenant1", ["file1"], "missing"))
    assert ok is False
    assert message == "Parent folder not found!"

    ok, data = _run(module.move_files("tenant1", ["file1"], "dest"))
    assert ok is True
    assert data is True
    assert moved == [("src", "old", "dest", "a.txt")]
    assert updated == [("file1", {"parent_id": "dest", "location": "a.txt"})]