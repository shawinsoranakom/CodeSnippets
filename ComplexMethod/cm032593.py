def test_trace_pipeline_task_routes_branch_matrix(monkeypatch, route_name, task_attr, empty_on_missing_task, error_text):
    if route_name in {"trace_graphrag", "trace_raptor"}:
        module = _dataset_sdk_routes_unit_module()
        if route_name == "trace_graphrag":
            module.test_run_trace_graphrag_matrix_unit(monkeypatch)
        else:
            module.test_run_trace_raptor_matrix_unit(monkeypatch)
        return

    module = _load_kb_module(monkeypatch)
    route = inspect.unwrap(getattr(module, route_name))

    def _make_kb(task_id):
        payload = {
            "id": "kb-1",
            "tenant_id": "tenant-1",
            "graphrag_task_id": "",
            "raptor_task_id": "",
            "mindmap_task_id": "",
        }
        payload[task_attr] = task_id
        return SimpleNamespace(**payload)

    _set_request_args(monkeypatch, module, {"kb_id": ""})
    res = route()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "KB ID" in res["message"], res

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1"})
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = route()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Invalid Knowledgebase ID" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _make_kb("")))
    res = route()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"] == {}, res

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _make_kb("task-1")))
    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (False, None))
    res = route()
    if empty_on_missing_task:
        assert res["code"] == module.RetCode.SUCCESS, res
        assert res["data"] == {}, res
    else:
        assert res["code"] == module.RetCode.DATA_ERROR, res
        assert error_text in res["message"], res

    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (True, _DummyTask("task-1", 1)))
    res = route()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["id"] == "task-1", res