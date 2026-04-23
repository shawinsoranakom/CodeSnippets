def test_upload_info_supports_url_single_and_multiple_files(monkeypatch):
    module = _load_document_app_module(monkeypatch)
    captured = []

    def fake_upload_info(user_id, file_obj, url=None):
        captured.append((user_id, getattr(file_obj, "filename", None), url))
        if url is not None:
            return {"kind": "url", "value": url}
        return {"kind": "file", "value": file_obj.filename}

    monkeypatch.setattr(module.FileService, "upload_info", fake_upload_info)

    monkeypatch.setattr(module, "request", _DummyRequest(files=_DummyFiles(), args={"url": "https://example.com/a.txt"}))
    res = _run(module.upload_info())
    assert res["code"] == 0
    assert res["data"] == {"kind": "url", "value": "https://example.com/a.txt"}

    monkeypatch.setattr(module, "request", _DummyRequest(files=_DummyFiles({"file": _DummyFile("single.txt")})))
    res = _run(module.upload_info())
    assert res["code"] == 0
    assert res["data"] == {"kind": "file", "value": "single.txt"}

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(files=_DummyFiles({"file": [_DummyFile("a.txt"), _DummyFile("b.txt")]})),
    )
    res = _run(module.upload_info())
    assert res["code"] == 0
    assert res["data"] == [
        {"kind": "file", "value": "a.txt"},
        {"kind": "file", "value": "b.txt"},
    ]
    assert captured == [
        ("user-1", None, "https://example.com/a.txt"),
        ("user-1", "single.txt", None),
        ("user-1", "a.txt", None),
        ("user-1", "b.txt", None),
    ]