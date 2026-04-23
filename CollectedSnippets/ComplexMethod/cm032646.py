def test_run_trace_graphrag_matrix_unit(monkeypatch):
    module = _load_dataset_module(monkeypatch)

    warnings = []
    monkeypatch.setattr(module.logging, "warning", lambda msg, *_args, **_kwargs: warnings.append(msg))

    res = _run(inspect.unwrap(module.run_graphrag)("tenant-1", ""))
    assert 'Dataset ID' in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.run_graphrag)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.DATA_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = _run(inspect.unwrap(module.run_graphrag)("tenant-1", "kb-1"))
    assert "Invalid Dataset ID" in res["message"], res

    stale_kb = _KB(kb_id="kb-1", graphrag_task_id="task-old")
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, stale_kb))
    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (False, None))
    monkeypatch.setattr(module.DocumentService, "get_by_kb_id", lambda **_kwargs: ([{"id": "doc-1"}], 1))
    monkeypatch.setattr(module.dataset_api_service, "queue_raptor_o_graphrag_tasks", lambda **_kwargs: "task-new")
    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: True)
    res = _run(inspect.unwrap(module.run_graphrag)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert any("GraphRAG" in msg for msg in warnings), warnings

    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (True, SimpleNamespace(progress=0)))
    res = _run(inspect.unwrap(module.run_graphrag)("tenant-1", "kb-1"))
    assert "already running" in res["message"], res

    warnings.clear()
    queue_calls = {}
    no_task_kb = _KB(kb_id="kb-1", graphrag_task_id="")
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, no_task_kb))
    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (False, None))
    monkeypatch.setattr(module.DocumentService, "get_by_kb_id", lambda **_kwargs: ([{"id": "doc-1"}, {"id": "doc-2"}], 2))

    def _queue(**kwargs):
        queue_calls.update(kwargs)
        return "queued-id"

    monkeypatch.setattr(module.dataset_api_service, "queue_raptor_o_graphrag_tasks", _queue)
    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.run_graphrag)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["graphrag_task_id"] == "queued-id", res
    assert queue_calls["doc_ids"] == ["doc-1", "doc-2"], queue_calls
    assert any("Cannot save graphrag_task_id" in msg for msg in warnings), warnings

    res = inspect.unwrap(module.trace_graphrag)("tenant-1", "")
    assert 'Dataset ID' in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = inspect.unwrap(module.trace_graphrag)("tenant-1", "kb-1")
    assert res["code"] == module.RetCode.DATA_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = inspect.unwrap(module.trace_graphrag)("tenant-1", "kb-1")
    assert "Invalid Dataset ID" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _KB(kb_id="kb-1", graphrag_task_id="task-1")))
    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (False, None))
    res = inspect.unwrap(module.trace_graphrag)("tenant-1", "kb-1")
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"] == {}, res

    monkeypatch.setattr(module.TaskService, "get_by_id", lambda _task_id: (True, SimpleNamespace(to_dict=lambda: {"id": _task_id, "progress": 1})))
    res = inspect.unwrap(module.trace_graphrag)("tenant-1", "kb-1")
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["id"] == "task-1", res