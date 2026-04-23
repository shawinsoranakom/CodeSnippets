def test_list_pipeline_dataset_logs_branches(monkeypatch):
    module = _load_kb_module(monkeypatch)

    _set_request_args(monkeypatch, module, {})
    _set_request_json(monkeypatch, module, {})
    res = _run(inspect.unwrap(module.list_pipeline_dataset_logs)())
    assert res["code"] == module.RetCode.ARGUMENT_ERROR, res
    assert "KB ID" in res["message"], res

    _set_request_args(
        monkeypatch,
        module,
        {
            "kb_id": "kb-1",
            "desc": "false",
            "create_date_from": "2025-01-01",
            "create_date_to": "2025-02-01",
        },
    )
    _set_request_json(monkeypatch, module, {})
    res = _run(inspect.unwrap(module.list_pipeline_dataset_logs)())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "Create data filter is abnormal." in res["message"], res

    _set_request_args(
        monkeypatch,
        module,
        {
            "kb_id": "kb-1",
            "page": "1",
            "page_size": "10",
            "desc": "false",
            "create_date_from": "2025-02-01",
            "create_date_to": "2025-01-01",
        },
    )
    _set_request_json(monkeypatch, module, {"operation_status": ["NOT_A_STATUS"]})
    res = _run(inspect.unwrap(module.list_pipeline_dataset_logs)())
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert "operation_status" in res["message"], res

    _set_request_args(
        monkeypatch,
        module,
        {
            "kb_id": "kb-1",
            "page": "1",
            "page_size": "10",
            "desc": "true",
            "create_date_from": "2025-02-01",
            "create_date_to": "2025-01-01",
        },
    )
    _set_request_json(monkeypatch, module, {"operation_status": []})
    monkeypatch.setattr(
        module.PipelineOperationLogService,
        "get_dataset_logs_by_kb_id",
        lambda *_args, **_kwargs: ([{"id": "l1"}], 1),
    )
    res = _run(inspect.unwrap(module.list_pipeline_dataset_logs)())
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["total"] == 1, res
    assert res["data"]["logs"][0]["id"] == "l1", res

    def _raise_dataset_logs(*_args, **_kwargs):
        raise RuntimeError("dataset logs boom")

    monkeypatch.setattr(module.PipelineOperationLogService, "get_dataset_logs_by_kb_id", _raise_dataset_logs)
    res = _run(inspect.unwrap(module.list_pipeline_dataset_logs)())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "dataset logs boom" in res["message"], res