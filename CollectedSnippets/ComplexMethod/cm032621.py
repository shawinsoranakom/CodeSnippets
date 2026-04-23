def test_rerun_and_cancel_matrix_unit(monkeypatch):
    module = _load_canvas_module(monkeypatch)
    _set_request_json(monkeypatch, module, {"id": "flow-1", "dsl": {"n": 1}, "component_id": "cmp-1"})

    monkeypatch.setattr(module.PipelineOperationLogService, "get_documents_info", lambda _id: [])
    res = _run(inspect.unwrap(module.rerun)())
    assert res["message"] == "Document not found."

    processing_doc = {"id": "doc-1", "name": "Doc-1", "kb_id": "kb-1", "progress": 0.5}
    monkeypatch.setattr(module.PipelineOperationLogService, "get_documents_info", lambda _id: [dict(processing_doc)])
    res = _run(inspect.unwrap(module.rerun)())
    assert "is processing" in res["message"]

    class _DocStore:
        def __init__(self):
            self.deleted = []

        def index_exist(self, *_args, **_kwargs):
            return True

        def delete(self, *args, **_kwargs):
            self.deleted.append(args)
            return True

    doc_store = _DocStore()
    monkeypatch.setattr(module.settings, "docStoreConn", doc_store)

    doc = {
        "id": "doc-1",
        "name": "Doc-1",
        "kb_id": "kb-1",
        "progress": 1.0,
        "progress_msg": "old",
        "chunk_num": 8,
        "token_num": 12,
    }
    updates = {"doc": [], "pipeline": [], "tasks": [], "queue": []}
    monkeypatch.setattr(module.PipelineOperationLogService, "get_documents_info", lambda _id: [dict(doc)])
    monkeypatch.setattr(module.DocumentService, "clear_chunk_num_when_rerun", lambda doc_id: updates["doc"].append(("clear", doc_id)))
    monkeypatch.setattr(module.DocumentService, "update_by_id", lambda doc_id, payload: updates["doc"].append(("update", doc_id, payload)))
    monkeypatch.setattr(module.TaskService, "filter_delete", lambda expr: updates["tasks"].append(expr))
    monkeypatch.setattr(module.PipelineOperationLogService, "update_by_id", lambda flow_id, payload: updates["pipeline"].append((flow_id, payload)))
    monkeypatch.setattr(
        module,
        "queue_dataflow",
        lambda **kwargs: updates["queue"].append(kwargs) or (True, ""),
    )
    monkeypatch.setattr(module, "get_uuid", lambda: "task-rerun")
    _set_request_json(monkeypatch, module, {"id": "flow-1", "dsl": {"n": 1}, "component_id": "cmp-1"})
    res = _run(inspect.unwrap(module.rerun)())
    assert res["code"] == module.RetCode.SUCCESS
    assert doc_store.deleted
    assert any(item[0] == "clear" and item[1] == "doc-1" for item in updates["doc"])
    assert updates["pipeline"] and updates["pipeline"][0][1]["dsl"]["path"] == ["cmp-1"]
    assert updates["queue"] and updates["queue"][0]["rerun"] is True

    redis_calls = []
    monkeypatch.setattr(module.REDIS_CONN, "set", lambda key, value: redis_calls.append((key, value)))
    res = module.cancel("task-9")
    assert res["code"] == module.RetCode.SUCCESS
    assert redis_calls == [("task-9-cancel", "x")]

    monkeypatch.setattr(module.REDIS_CONN, "set", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("redis fail")))
    res = module.cancel("task-9")
    assert res["code"] == module.RetCode.SUCCESS