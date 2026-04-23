def test_unbind_task_branch_matrix(monkeypatch):
    module = _load_kb_module(monkeypatch)
    route = inspect.unwrap(module.delete_kb_task)

    _set_request_args(monkeypatch, module, {"kb_id": ""})
    res = route()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "KB ID" in res["message"], res

    _set_request_args(monkeypatch, module, {"kb_id": "missing", "pipeline_task_type": module.PipelineTaskType.GRAPH_RAG})
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (False, None))
    res = route()
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"] is True, res

    kb = SimpleNamespace(
        id="kb-1",
        tenant_id="tenant-1",
        graphrag_task_id="graph-task",
        raptor_task_id="raptor-task",
        mindmap_task_id="mindmap-task",
    )
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, kb))
    _set_request_args(monkeypatch, module, {"kb_id": "kb-1", "pipeline_task_type": "unknown"})
    res = route()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Invalid task type" in res["message"], res

    cancelled = []
    deleted = []
    update_payloads = []
    monkeypatch.setattr(module.REDIS_CONN, "set", lambda key, value: cancelled.append((key, value)))
    monkeypatch.setattr(module.search, "index_name", lambda _tenant_id: "idx")
    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(delete=lambda *args, **_kwargs: deleted.append(args)))

    def _record_update(_kb_id, payload):
        update_payloads.append((_kb_id, payload))
        return True

    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", _record_update)

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1", "pipeline_task_type": module.PipelineTaskType.GRAPH_RAG})
    res = route()
    assert res["code"] == module.RetCode.SUCCESS, res

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1", "pipeline_task_type": module.PipelineTaskType.RAPTOR})
    res = route()
    assert res["code"] == module.RetCode.SUCCESS, res

    _set_request_args(monkeypatch, module, {"kb_id": "kb-1", "pipeline_task_type": module.PipelineTaskType.MINDMAP})
    res = route()
    assert res["code"] == module.RetCode.SUCCESS, res

    assert ("graph-task-cancel", "x") in cancelled, cancelled
    assert ("raptor-task-cancel", "x") in cancelled, cancelled
    assert ("mindmap-task-cancel", "x") in cancelled, cancelled
    assert len(deleted) == 2, deleted
    assert any(payload.get("graphrag_task_id") == "" for _, payload in update_payloads), update_payloads
    assert any(payload.get("raptor_task_id") == "" for _, payload in update_payloads), update_payloads
    assert any(payload.get("mindmap_task_id") == "" for _, payload in update_payloads), update_payloads

    class _FlakyPipelineType:
        def __init__(self, target):
            self.target = target
            self.calls = 0

        def __eq__(self, other):
            self.calls += 1
            if self.calls == 1:
                return other == self.target
            return False

    _set_request_args(
        monkeypatch,
        module,
        {"kb_id": "kb-1", "pipeline_task_type": _FlakyPipelineType(module.PipelineTaskType.GRAPH_RAG)},
    )
    res = route()
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Internal Error: Invalid task type" in res["message"], res

    monkeypatch.setattr(module.KnowledgebaseService, "update_by_id", lambda *_args, **_kwargs: False)
    monkeypatch.setattr(module, "server_error_response", lambda e: module.get_json_result(code=module.RetCode.EXCEPTION_ERROR, message=str(e)))
    _set_request_args(monkeypatch, module, {"kb_id": "kb-1", "pipeline_task_type": module.PipelineTaskType.GRAPH_RAG})
    res = route()
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "cannot delete task" in res["message"], res