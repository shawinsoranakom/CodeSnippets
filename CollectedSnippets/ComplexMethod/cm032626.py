def test_session_crud_prompts_and_download_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    class _SessionCanvas:
        def __init__(self, *_args, **_kwargs):
            self.reset_called = False

        def reset(self):
            self.reset_called = True

    _set_request_json(monkeypatch, module, {"name": "Sess1"})
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (True, SimpleNamespace(id="canvas-1", dsl={"n": 1})))
    monkeypatch.setattr(module, "Canvas", _SessionCanvas)
    monkeypatch.setattr(module, "get_uuid", lambda: "sess-1")
    saved = []
    monkeypatch.setattr(module.API4ConversationService, "save", lambda **kwargs: saved.append(kwargs))
    res = _run(inspect.unwrap(module.set_session)("canvas-1"))
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["id"] == "sess-1"
    assert isinstance(res["data"]["dsl"], str)
    assert saved and saved[-1]["id"] == "sess-1"

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = module.get_session("canvas-1", "sess-1")
    assert res["code"] == module.RetCode.OPERATING_ERROR

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.API4ConversationService, "get_by_id", lambda _session_id: (True, SimpleNamespace(to_dict=lambda: {"id": _session_id})))
    res = module.get_session("canvas-1", "sess-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["id"] == "sess-1"

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = module.del_session("canvas-1", "sess-1")
    assert res["code"] == module.RetCode.OPERATING_ERROR

    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.API4ConversationService, "delete_by_id", lambda _session_id: _session_id == "sess-1")
    res = module.del_session("canvas-1", "sess-1")
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"] is True

    rag_prompts_pkg = ModuleType("rag.prompts")
    rag_prompts_pkg.__path__ = []
    monkeypatch.setitem(sys.modules, "rag.prompts", rag_prompts_pkg)
    rag_generator_mod = ModuleType("rag.prompts.generator")
    rag_generator_mod.ANALYZE_TASK_SYSTEM = "SYS"
    rag_generator_mod.ANALYZE_TASK_USER = "USER"
    rag_generator_mod.NEXT_STEP = "NEXT"
    rag_generator_mod.REFLECT = "REFLECT"
    rag_generator_mod.CITATION_PROMPT_TEMPLATE = "CITE"
    monkeypatch.setitem(sys.modules, "rag.prompts.generator", rag_generator_mod)

    res = module.prompts()
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["task_analysis"] == "SYS\n\nUSER"
    assert res["data"]["plan_generation"] == "NEXT"
    assert res["data"]["reflection"] == "REFLECT"
    assert res["data"]["citation_guidelines"] == "CITE"

    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({"id": "f1", "created_by": "u1"})))
    monkeypatch.setattr(module.FileService, "get_blob", lambda _created_by, _id: b"blob-data")
    res = _run(module.download())
    assert res == {"blob": b"blob-data"}