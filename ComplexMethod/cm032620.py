def test_run_dataflow_and_canvas_sse_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)

    async def _thread_pool_exec(func, *args, **kwargs):
        return func(*args, **kwargs)

    monkeypatch.setattr(module, "thread_pool_exec", _thread_pool_exec)

    _set_request_json(monkeypatch, module, {"id": "c1"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.run)())
    assert res["code"] == module.RetCode.OPERATING_ERROR

    _set_request_json(monkeypatch, module, {"id": "c1"})
    monkeypatch.setattr(module.UserCanvasService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.CanvasReplicaService, "load_for_run", lambda *_args, **_kwargs: None)
    res = _run(inspect.unwrap(module.run)())
    assert res["message"] == "canvas replica not found, please call /get/<canvas_id> first."

    _set_request_json(monkeypatch, module, {"id": "ag-1", "query": "q", "files": [], "inputs": {}})
    monkeypatch.setattr(module.CanvasReplicaService, "load_for_run", lambda *_args, **_kwargs: {"dsl": {"x": 1}, "title": "ag", "canvas_category": module.CanvasCategory.Agent})
    monkeypatch.setattr(module, "Canvas", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("canvas init failed")))
    res = _run(inspect.unwrap(module.run)())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "canvas init failed" in res["message"]

    updates = []

    class _CanvasSSESuccess:
        def __init__(self, *_args, **_kwargs):
            self.cancelled = False

        async def run(self, **_kwargs):
            yield {"answer": "stream-ok"}

        def cancel_task(self):
            self.cancelled = True

        def __str__(self):
            return '{"updated": true}'

    _set_request_json(monkeypatch, module, {"id": "ag-2", "query": "q", "files": [], "inputs": {}, "user_id": "exp-2"})
    monkeypatch.setattr(module, "Canvas", _CanvasSSESuccess)
    monkeypatch.setattr(module.CanvasReplicaService, "load_for_run", lambda *_args, **_kwargs: {"dsl": {}, "title": "ag2", "canvas_category": module.CanvasCategory.Agent})
    monkeypatch.setattr(module.UserCanvasService, "update_by_id", lambda canvas_id, payload: updates.append((canvas_id, payload)))
    resp = _run(inspect.unwrap(module.run)())
    assert isinstance(resp, _StubResponse)
    assert resp.headers.get("Content-Type") == "text/event-stream; charset=utf-8"
    chunks = _run(_collect_stream(resp.response))
    assert any('"answer": "stream-ok"' in chunk for chunk in chunks)

    class _CanvasSSEError:
        last_instance = None

        def __init__(self, *_args, **_kwargs):
            self.cancelled = False
            _CanvasSSEError.last_instance = self

        async def run(self, **_kwargs):
            yield {"answer": "start"}
            raise RuntimeError("stream boom")

        def cancel_task(self):
            self.cancelled = True

        def __str__(self):
            return "{}"

    _set_request_json(monkeypatch, module, {"id": "ag-3", "query": "q", "files": [], "inputs": {}, "user_id": "exp-3"})
    monkeypatch.setattr(module, "Canvas", _CanvasSSEError)
    monkeypatch.setattr(module.CanvasReplicaService, "load_for_run", lambda *_args, **_kwargs: {"dsl": {}, "title": "ag3", "canvas_category": module.CanvasCategory.Agent})
    resp = _run(inspect.unwrap(module.run)())
    chunks = _run(_collect_stream(resp.response))
    assert any('"code": 500' in chunk and "stream boom" in chunk for chunk in chunks)
    assert _CanvasSSEError.last_instance.cancelled is True