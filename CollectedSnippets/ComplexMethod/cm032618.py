def test_templates_rm_save_get_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    class _Template:
        def __init__(self, template_id):
            self.template_id = template_id

        def to_dict(self):
            return {"id": self.template_id, "canvas_type": "Recommended", "canvas_types": ["Recommended", "Agent"]}

    monkeypatch.setattr(module.CanvasTemplateService, "get_all", lambda: [_Template("tpl-1")])
    res = module.templates()
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"] == [{"id": "tpl-1", "canvas_type": "Recommended", "canvas_types": ["Recommended", "Agent"]}]

    _set_request_json(monkeypatch, module, {"canvas_ids": ["c1", "c2"]})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.rm)())
    assert res["code"] == module.RetCode.OPERATING_ERROR
    assert "Only owner of canvas authorized" in res["message"]

    deleted = []
    _set_request_json(monkeypatch, module, {"canvas_ids": ["c1", "c2"]})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserCanvasService, "delete_by_id", lambda canvas_id: deleted.append(canvas_id))
    res = _run(inspect.unwrap(module.rm)())
    assert res["data"] is True
    assert deleted == ["c1", "c2"]

    _set_request_json(monkeypatch, module, {"title": "  Demo  ", "dsl": {"n": 1}})
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [object()])
    res = _run(inspect.unwrap(module.save)())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "already exists" in res["message"]

    _set_request_json(monkeypatch, module, {"title": "Demo", "dsl": {"n": 1}})
    monkeypatch.setattr(module, "get_uuid", lambda: "canvas-new")
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    monkeypatch.setattr(module.UserCanvasService, "save", lambda **_kwargs: False)
    res = _run(inspect.unwrap(module.save)())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "Fail to save canvas." in res["message"]

    created = {"save": [], "versions": []}
    _set_request_json(monkeypatch, module, {"title": "Demo", "dsl": {"n": 1}})
    monkeypatch.setattr(module, "get_uuid", lambda: "canvas-new")
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    monkeypatch.setattr(module.UserCanvasService, "save", lambda **kwargs: created["save"].append(kwargs) or True)
    monkeypatch.setattr(module.UserCanvasVersionService, "save_or_replace_latest", lambda *_args, **kwargs: created["versions"].append(("save_or_replace_latest", kwargs)))
    res = _run(inspect.unwrap(module.save)())
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["id"] == "canvas-new"
    assert created["save"]
    assert any(item[0] == "save_or_replace_latest" for item in created["versions"])

    _set_request_json(monkeypatch, module, {"id": "canvas-1", "title": "Renamed", "dsl": "{\"m\": 1}"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.save)())
    assert res["code"] == module.RetCode.OPERATING_ERROR

    updates = []
    versions = []
    _set_request_json(monkeypatch, module, {"id": "canvas-1", "title": "Renamed", "dsl": "{\"m\": 1}"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserCanvasService, "update_by_id", lambda canvas_id, payload: updates.append((canvas_id, payload)))
    monkeypatch.setattr(module.UserCanvasVersionService, "save_or_replace_latest", lambda *_args, **kwargs: versions.append(("save_or_replace_latest", kwargs)))
    res = _run(inspect.unwrap(module.save)())
    assert res["code"] == module.RetCode.SUCCESS
    assert updates and updates[0][0] == "canvas-1"
    assert any(item[0] == "save_or_replace_latest" for item in versions)

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = module.get("canvas-1")
    assert res["code"] == module.RetCode.DATA_ERROR
    assert res["message"] == "canvas not found."

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserCanvasService, "get_by_canvas_id", lambda _canvas_id: (True, {"id": "canvas-1"}))
    res = module.get("canvas-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["id"] == "canvas-1"