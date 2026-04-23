def test_convert_branch_matrix_unit(monkeypatch):
    module = _load_file2document_module(monkeypatch)
    req_state = {"kb_ids": ["kb-1"], "file_ids": ["f1"]}
    _set_request_json(monkeypatch, module, req_state)

    # Falsy file → "File not found!" (synchronous validation)
    monkeypatch.setattr(module.FileService, "get_by_ids", lambda _ids: [_FalsyFile("f1", module.FileType.DOC.value)])
    res = _run(module.convert())
    assert res["message"] == "File not found!"

    # Valid file but invalid kb → "Can't find this dataset!" (synchronous validation)
    # KnowledgebaseService stub returns (False, None) by default
    monkeypatch.setattr(module.FileService, "get_by_ids", lambda _ids: [_DummyFile("f1", module.FileType.DOC.value)])
    res = _run(module.convert())
    assert res["message"] == "Can't find this dataset!"

    # Valid file and kb → schedules background work, returns data=True immediately
    kb = SimpleNamespace(id="kb-1", parser_id="naive", pipeline_id="p1", parser_config={})
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, kb))
    res = _run(module.convert())
    assert res["code"] == 0
    assert res["data"] is True

    # Folder expansion → schedules background work, returns data=True immediately
    req_state["file_ids"] = ["folder-1"]
    monkeypatch.setattr(module.FileService, "get_by_ids", lambda _ids: [_DummyFile("folder-1", module.FileType.FOLDER.value, name="folder")])
    monkeypatch.setattr(module.FileService, "get_all_innermost_file_ids", lambda _file_id, _acc: ["inner-1"])
    res = _run(module.convert())
    assert res["code"] == 0
    assert res["data"] is True

    # Exception in file lookup → 500
    req_state["file_ids"] = ["f1"]
    monkeypatch.setattr(
        module.FileService,
        "get_by_ids",
        lambda _ids: (_ for _ in ()).throw(RuntimeError("convert boom")),
    )
    res = _run(module.convert())
    assert res["code"] == 500
    assert "convert boom" in res["message"]