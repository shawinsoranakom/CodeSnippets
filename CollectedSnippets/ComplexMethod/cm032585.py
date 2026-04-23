def test_compare_export_and_evaluate_single_matrix_unit(monkeypatch):
    module = _load_evaluation_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"run_ids": ["run-1"]})
    res = _run(module.compare_runs())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "at least 2" in res["message"]

    _set_request_json(monkeypatch, module, {"run_ids": ["run-1", "run-2"]})
    res = _run(module.compare_runs())
    assert res["code"] == 0
    assert res["data"]["comparison"] == {}

    def _raise_json_compare(*_args, **_kwargs):
        raise RuntimeError("compare boom")

    monkeypatch.setattr(module, "get_json_result", _raise_json_compare)
    _set_request_json(monkeypatch, module, {"run_ids": ["run-1", "run-2", "run-3"]})
    res = _run(module.compare_runs())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "compare boom" in res["message"]

    monkeypatch.setattr(module, "get_json_result", lambda code=0, message="success", data=None: {"code": code, "message": message, "data": data})
    monkeypatch.setattr(module.EvaluationService, "get_run_results", lambda _run_id: None)
    res = _run(module.export_results("run-11"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "not found" in res["message"].lower()

    monkeypatch.setattr(module.EvaluationService, "get_run_results", lambda _run_id: {"id": _run_id, "rows": []})
    res = _run(module.export_results("run-12"))
    assert res["code"] == 0
    assert res["data"]["id"] == "run-12"

    def _raise_export(_run_id):
        raise RuntimeError("export boom")

    monkeypatch.setattr(module.EvaluationService, "get_run_results", _raise_export)
    res = _run(module.export_results("run-13"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "export boom" in res["message"]

    monkeypatch.setattr(module, "get_json_result", lambda code=0, message="success", data=None: {"code": code, "message": message, "data": data})
    res = _run(module.evaluate_single())
    assert res["code"] == 0
    assert res["data"]["answer"] == ""
    assert res["data"]["metrics"] == {}
    assert res["data"]["retrieved_chunks"] == []

    def _raise_json_single(*_args, **_kwargs):
        raise RuntimeError("single boom")

    monkeypatch.setattr(module, "get_json_result", _raise_json_single)
    res = _run(module.evaluate_single())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "single boom" in res["message"]