def test_run_pipeline_task_routes_branch_matrix(monkeypatch, route_name, task_attr, response_key, task_type):
    if route_name in {"run_graphrag", "run_raptor"}:
        module = _dataset_sdk_routes_unit_module()
        if route_name == "run_graphrag":
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

    warnings = []
    monkeypatch.setattr(module.logging, "warning", lambda msg, *_args, **_kwargs: warnings.append(msg))

    _set_request_json(monkeypatch, module, {"kb_id": ""})
    res = _run(route())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "KB ID" in res["message"], res

    _set_request_json(monkeypatch, module, {"kb_id": "kb-1"})
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = _run(route())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Invalid Knowledgebase ID" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _make_kb("task-running")))
    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (True, SimpleNamespace(progress=0)))
    res = _run(route())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "already running" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _make_kb("task-stale")))
    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (False, None))
    monkeypatch.setattr(module.DocumentService, "get_by_kb_id", lambda **_kwargs: ([], 0))
    res = _run(route())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "No documents in Knowledgebase kb-1" in res["message"], res
    assert warnings, "Expected warning for stale task id"

    queue_calls = {}

    def _queue_stub(**kwargs):
        queue_calls.update(kwargs)
        return "queued-task-id"

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _make_kb("")))
    monkeypatch.setattr(
        module.DocumentService,
        "get_by_kb_id",
        lambda **_kwargs: ([{"id": "doc-1"}, {"id": "doc-2"}], 2),
    )
    monkeypatch.setattr(module, "queue_raptor_o_graphrag_tasks", _queue_stub)
    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: False)
    res = _run(route())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"][response_key] == "queued-task-id", res
    assert queue_calls["ty"] == task_type, queue_calls
    assert queue_calls["doc_ids"] == ["doc-1", "doc-2"], queue_calls