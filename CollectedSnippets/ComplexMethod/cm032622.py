def test_reset_upload_input_form_debug_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    _set_request_json(monkeypatch, module, {"id": "canvas-1"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.reset)())
    assert res["code"] == module.RetCode.OPERATING_ERROR

    _set_request_json(monkeypatch, module, {"id": "canvas-1"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (False, None))
    res = _run(inspect.unwrap(module.reset)())
    assert res["message"] == "canvas not found."

    class _ResetCanvas:
        def __init__(self, *_args, **_kwargs):
            self.reset_called = False

        def reset(self):
            self.reset_called = True

        def __str__(self):
            return '{"v": 2}'

    updates = []
    _set_request_json(monkeypatch, module, {"id": "canvas-1"})
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (True, SimpleNamespace(id="canvas-1", dsl={"v": 1})))
    monkeypatch.setattr(module.UserCanvasService, "update_by_id", lambda canvas_id, payload: updates.append((canvas_id, payload)))
    monkeypatch.setattr(module, "Canvas", _ResetCanvas)
    res = _run(inspect.unwrap(module.reset)())
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"] == {"v": 2}
    assert updates == [("canvas-1", {"dsl": {"v": 2}})]

    _set_request_json(monkeypatch, module, {"id": "canvas-1"})
    monkeypatch.setattr(module, "Canvas", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("reset boom")))
    res = _run(inspect.unwrap(module.reset)())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "reset boom" in res["message"]

    monkeypatch.setattr(module.UserCanvasService, "get_by_canvas_id", lambda _canvas_id: (False, None))
    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({"url": "http://example.com"}), files=_FileMap()))
    res = _run(module.upload("canvas-1"))
    assert res["message"] == "canvas not found."

    monkeypatch.setattr(module.UserCanvasService, "get_by_canvas_id", lambda _canvas_id: (True, {"user_id": "tenant-1"}))
    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(
            args=_Args({"url": "http://example.com"}),
            files=_FileMap({"file": ["file-1"]}),
        ),
    )
    monkeypatch.setattr(module.FileService, "upload_info", lambda user_id, file_obj, url=None: {"uid": user_id, "file": file_obj, "url": url})
    res = _run(module.upload("canvas-1"))
    assert res["data"]["url"] == "http://example.com"

    monkeypatch.setattr(
        module,
        "request",
        _DummyRequest(
            args=_Args({"url": "http://example.com"}),
            files=_FileMap({"file": ["f1", "f2"]}),
        ),
    )
    monkeypatch.setattr(module.FileService, "upload_info", lambda user_id, file_obj, url=None: {"uid": user_id, "file": file_obj, "url": url})
    res = _run(module.upload("canvas-1"))
    assert len(res["data"]) == 2

    monkeypatch.setattr(module.FileService, "upload_info", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("upload boom")))
    res = _run(module.upload("canvas-1"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "upload boom" in res["message"]

    monkeypatch.setattr(module, "request", _DummyRequest(args=_Args({"id": "canvas-1", "component_id": "begin"})))
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (False, None))
    res = module.input_form()
    assert res["message"] == "canvas not found."

    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (True, SimpleNamespace(id="canvas-1", dsl={"n": 1})))
    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [])
    res = module.input_form()
    assert res["code"] == module.RetCode.OPERATING_ERROR

    class _InputCanvas:
        def __init__(self, *_args, **_kwargs):
            pass

        def get_component_input_form(self, component_id):
            return {"component_id": component_id}

    monkeypatch.setattr(module.UserCanvasService, "query", lambda **_kwargs: [object()])
    monkeypatch.setattr(module, "Canvas", _InputCanvas)
    res = module.input_form()
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["component_id"] == "begin"

    monkeypatch.setattr(module, "Canvas", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("input boom")))
    res = module.input_form()
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "input boom" in res["message"]

    _set_request_json(
        monkeypatch,
        module,
        {"id": "canvas-1", "component_id": "llm-node", "params": {"p": {"value": "v"}}},
    )
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.debug)())
    assert res["code"] == module.RetCode.OPERATING_ERROR

    class _DebugComponent(module.LLM):
        def __init__(self):
            self.reset_called = False
            self.debug_inputs = None
            self.invoked = None

        def reset(self):
            self.reset_called = True

        def set_debug_inputs(self, params):
            self.debug_inputs = params

        def invoke(self, **kwargs):
            self.invoked = kwargs

        def output(self):
            async def _gen():
                yield "A"
                yield "B"

            return {"stream": partial(_gen)}

    class _DebugCanvas:
        last_component = None

        def __init__(self, *_args, **_kwargs):
            self.message_id = ""
            self._component = _DebugComponent()
            _DebugCanvas.last_component = self._component

        def reset(self):
            return None

        def get_component(self, _component_id):
            return {"obj": self._component}

    _set_request_json(
        monkeypatch,
        module,
        {"id": "canvas-1", "component_id": "llm-node", "params": {"p": {"value": "v"}}},
    )
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.UserCanvasService, "get_by_id", lambda _canvas_id: (True, SimpleNamespace(id="canvas-1", dsl={"n": 1})))
    monkeypatch.setattr(module, "get_uuid", lambda: "msg-1")
    monkeypatch.setattr(module, "Canvas", _DebugCanvas)
    res = _run(inspect.unwrap(module.debug)())
    assert res["code"] == module.RetCode.SUCCESS
    assert res["data"]["stream"] == "AB"
    assert _DebugCanvas.last_component.reset_called is True
    assert _DebugCanvas.last_component.debug_inputs == {"p": {"value": "v"}}
    assert _DebugCanvas.last_component.invoked == {"p": "v"}