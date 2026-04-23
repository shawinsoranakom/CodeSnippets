def test_pipeline_log_detail_and_delete_routes_branches(monkeypatch):
    module = _load_kb_module(monkeypatch)

    _set_request_args(monkeypatch, module, {})
    _set_request_json(monkeypatch, module, {})
    res = _run(inspect.unwrap(module.delete_pipeline_logs)())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res
    assert "KB ID" in res["message"], res

    deleted_ids = []

    def _delete_by_ids(log_ids):
        deleted_ids.extend(log_ids)

    monkeypatch.setattr(module.PipelineOperationLogService, "delete_by_ids", _delete_by_ids)
    _set_request_args(monkeypatch, module, {"kb_id": "kb-1"})
    _set_request_json(monkeypatch, module, {})
    res = _run(inspect.unwrap(module.delete_pipeline_logs)())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"] is True, res
    assert deleted_ids == [], deleted_ids

    _set_request_json(monkeypatch, module, {"log_ids": ["l1", "l2"]})
    res = _run(inspect.unwrap(module.delete_pipeline_logs)())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert deleted_ids == ["l1", "l2"], deleted_ids

    _set_request_args(monkeypatch, module, {})
    res = inspect.unwrap(module.pipeline_log_detail)()
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res
    assert "Pipeline log ID" in res["message"], res

    _set_request_args(monkeypatch, module, {"log_id": "missing"})
    monkeypatch.setattr(module.PipelineOperationLogService, "get_by_id", lambda _log_id: (False, None))
    res = inspect.unwrap(module.pipeline_log_detail)()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Invalid pipeline log ID" in res["message"], res

    class _Log:
        def to_dict(self):
            return {"id": "log-1", "status": "ok"}

    monkeypatch.setattr(module.PipelineOperationLogService, "get_by_id", lambda _log_id: (True, _Log()))
    res = inspect.unwrap(module.pipeline_log_detail)()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["id"] == "log-1", res