def test_canvas_history_list_and_setting_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    class _Version:
        def __init__(self, version_id, update_time):
            self.version_id = version_id
            self.update_time = update_time

        def to_dict(self):
            return {"id": self.version_id, "update_time": self.update_time}

    monkeypatch.setattr(
        module.UserCanvasVersionService,
        "list_by_canvas_id",
        lambda _canvas_id: [_Version("v1", 1), _Version("v2", 5)],
    )
    res = module.getlistversion("canvas-1")
    assert [item["id"] for item in res["data"]] == ["v2", "v1"]

    monkeypatch.setattr(
        module.UserCanvasVersionService,
        "list_by_canvas_id",
        lambda _canvas_id: (_ for _ in ()).throw(RuntimeError("history boom")),
    )
    res = module.getlistversion("canvas-1")
    assert "Error getting history files: history boom" in res["message"]

    monkeypatch.setattr(
        module.UserCanvasVersionService,
        "get_by_id",
        lambda _version_id: (True, _Version("v3", 3)),
    )
    res = module.getversion("v3")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["id"] == "v3"

    monkeypatch.setattr(
        module.UserCanvasVersionService,
        "get_by_id",
        lambda _version_id: (_ for _ in ()).throw(RuntimeError("version boom")),
    )
    res = module.getversion("v3")
    assert "Error getting history file: version boom" in res["data"]

    list_calls = []

    def _get_by_tenant_ids(tenants, user_id, page_number, page_size, orderby, desc, keywords, canvas_category):
        list_calls.append((tenants, user_id, page_number, page_size, orderby, desc, keywords, canvas_category))
        return [{"id": "canvas-1"}], 1

    monkeypatch.setattr(module.UserCanvasService, "get_by_tenant_ids", _get_by_tenant_ids)
    monkeypatch.setattr(
        module.TenantService,
        "get_joined_tenants_by_user_id",
        lambda _user_id: [{"tenant_id": "t1"}, {"tenant_id": "t2"}],
    )

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(
            args=_Args(
                {
                    "keywords": "kw",
                    "page": "2",
                    "page_size": "3",
                    "orderby": "update_time",
                    "canvas_category": "agent",
                    "desc": "false",
                }
            )
        ),
    )
    res = module.list_canvas()
    assert res["code"] == module.RetCode.SUCCESS
    assert list_calls[-1][0] == ["t1", "t2", "user-1"]
    assert list_calls[-1][2:6] == (2, 3, "update_time", False)

    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({"owner_ids": "u1,u2", "desc": "true"})))
    res = module.list_canvas()
    assert res["code"] == module.RetCode.SUCCESS
    assert list_calls[-1][0] == ["u1", "u2"]
    assert list_calls[-1][2:4] == (0, 0)
    assert list_calls[-1][5] is True

    _set_request_json(monkeypatch, module, {"id": "canvas-1", "title": "T", "permission": "private"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.setting)())
    assert res["code"] == module.RetCode.OPERATING_ERROR

    _set_request_json(monkeypatch, module, {"id": "canvas-1", "title": "T", "permission": "private"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (False, None))
    res = _run(inspect.unwrap(module.setting)())
    assert res["message"] == "canvas not found."

    updates = []
    _set_request_json(
        monkeypatch,
        module,
        {
            "id": "canvas-1",
            "title": "New title",
            "permission": "private",
            "description": "new desc",
            "avatar": "avatar.png",
        },
    )
    monkeypatch.setattr(
        module.UserCanvasService,
        "get_by_id",
        lambda _canvas_id: (True, SimpleNamespace(to_dict=lambda: {"id": "canvas-1", "title": "Old"})),
    )
    monkeypatch.setattr(module.UserCanvasService, "update_by_id", lambda canvas_id, payload: updates.append((canvas_id, payload)) or 2)
    res = _run(inspect.unwrap(module.setting)())
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"] == 2
    assert updates[-1][0] == "canvas-1"
    assert updates[-1][1]["title"] == "New title"
    assert updates[-1][1]["description"] == "new desc"
    assert updates[-1][1]["permission"] == "private"
    assert updates[-1][1]["avatar"] == "avatar.png"