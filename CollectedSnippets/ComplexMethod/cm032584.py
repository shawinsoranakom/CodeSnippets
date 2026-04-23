def test_run_and_recommendation_routes_matrix_unit(monkeypatch):
    module = _load_evaluation_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"dataset_id": "d1", "dialog_id": "dialog-1", "name": "run 1"})
    monkeypatch.setattr(module.EvaluationService, "start_evaluation", lambda **_kwargs: (False, "start failed"))
    res = _run(module.start_evaluation())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "start failed" in res["message"]

    monkeypatch.setattr(module.EvaluationService, "start_evaluation", lambda **_kwargs: (True, "run-ok"))
    res = _run(module.start_evaluation())
    assert res["code"] == 0
    assert res["data"]["run_id"] == "run-ok"

    def _raise_start(**_kwargs):
        raise RuntimeError("start boom")

    monkeypatch.setattr(module.EvaluationService, "start_evaluation", _raise_start)
    res = _run(module.start_evaluation())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "start boom" in res["message"]

    monkeypatch.setattr(module.EvaluationService, "get_run_results", lambda _run_id: None)
    res = _run(module.get_evaluation_run("run-1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "not found" in res["message"].lower()

    monkeypatch.setattr(module.EvaluationService, "get_run_results", lambda _run_id: {"id": _run_id})
    res = _run(module.get_evaluation_run("run-2"))
    assert res["code"] == 0
    assert res["data"]["id"] == "run-2"

    def _raise_get_run(_run_id):
        raise RuntimeError("get run boom")

    monkeypatch.setattr(module.EvaluationService, "get_run_results", _raise_get_run)
    res = _run(module.get_evaluation_run("run-3"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "get run boom" in res["message"]

    monkeypatch.setattr(module.EvaluationService, "get_run_results", lambda _run_id: None)
    res = _run(module.get_run_results("run-4"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "not found" in res["message"].lower()

    monkeypatch.setattr(module.EvaluationService, "get_run_results", lambda _run_id: {"id": _run_id, "score": 0.9})
    res = _run(module.get_run_results("run-5"))
    assert res["code"] == 0
    assert res["data"]["id"] == "run-5"

    def _raise_results(_run_id):
        raise RuntimeError("get results boom")

    monkeypatch.setattr(module.EvaluationService, "get_run_results", _raise_results)
    res = _run(module.get_run_results("run-6"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "get results boom" in res["message"]

    res = _run(module.list_evaluation_runs())
    assert res["code"] == 0
    assert res["data"]["total"] == 0

    def _raise_json_list(*_args, **_kwargs):
        raise RuntimeError("list runs boom")

    monkeypatch.setattr(module, "get_json_result", _raise_json_list)
    res = _run(module.list_evaluation_runs())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "list runs boom" in res["message"]

    monkeypatch.setattr(module, "get_json_result", lambda code=0, message="success", data=None: {"code": code, "message": message, "data": data})
    res = _run(module.delete_evaluation_run("run-7"))
    assert res["code"] == 0
    assert res["data"]["run_id"] == "run-7"

    def _raise_json_delete(*_args, **_kwargs):
        raise RuntimeError("delete run boom")

    monkeypatch.setattr(module, "get_json_result", _raise_json_delete)
    res = _run(module.delete_evaluation_run("run-8"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "delete run boom" in res["message"]

    monkeypatch.setattr(module, "get_json_result", lambda code=0, message="success", data=None: {"code": code, "message": message, "data": data})
    monkeypatch.setattr(module.EvaluationService, "get_recommendations", lambda _run_id: [{"name": "cfg-1"}])
    res = _run(module.get_recommendations("run-9"))
    assert res["code"] == 0
    assert res["data"]["recommendations"][0]["name"] == "cfg-1"

    def _raise_recommend(_run_id):
        raise RuntimeError("recommend boom")

    monkeypatch.setattr(module.EvaluationService, "get_recommendations", _raise_recommend)
    res = _run(module.get_recommendations("run-10"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "recommend boom" in res["message"]