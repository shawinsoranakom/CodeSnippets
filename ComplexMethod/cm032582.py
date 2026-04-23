def test_dataset_routes_matrix_unit(monkeypatch):
    module = _load_evaluation_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"name": "  data-1  ", "description": "desc", "kb_ids": ["kb-1"]})
    monkeypatch.setattr(module.EvaluationService, "create_dataset", lambda **_kwargs: (True, "dataset-ok"))
    res = _run(module.create_dataset())
    assert res["code"] == 0
    assert res["data"]["dataset_id"] == "dataset-ok"

    _set_request_json(monkeypatch, module, {"name": "   ", "kb_ids": ["kb-1"]})
    res = _run(module.create_dataset())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "empty" in res["message"].lower()

    _set_request_json(monkeypatch, module, {"name": "data-2", "kb_ids": "kb-1"})
    res = _run(module.create_dataset())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "kb_ids" in res["message"]

    _set_request_json(monkeypatch, module, {"name": "data-3", "kb_ids": ["kb-1"]})
    monkeypatch.setattr(module.EvaluationService, "create_dataset", lambda **_kwargs: (False, "create failed"))
    res = _run(module.create_dataset())
    assert res["code"] == module.RetCode.DATA_ERROR
    assert res["message"] == "create failed"

    def _raise_create(**_kwargs):
        raise RuntimeError("create boom")

    monkeypatch.setattr(module.EvaluationService, "create_dataset", _raise_create)
    res = _run(module.create_dataset())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "create boom" in res["message"]

    _set_request_args(monkeypatch, module, {"page": "2", "page_size": "3"})
    monkeypatch.setattr(module.EvaluationService, "list_datasets", lambda **_kwargs: {"datasets": [{"id": "a"}], "total": 1})
    res = _run(module.list_datasets())
    assert res["code"] == 0
    assert res["data"]["total"] == 1

    _set_request_args(monkeypatch, module, {"page": "x"})
    res = _run(module.list_datasets())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR

    monkeypatch.setattr(module.EvaluationService, "get_dataset", lambda _dataset_id: None)
    res = _run(module.get_dataset("dataset-1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "not found" in res["message"].lower()

    monkeypatch.setattr(module.EvaluationService, "get_dataset", lambda _dataset_id: {"id": _dataset_id})
    res = _run(module.get_dataset("dataset-2"))
    assert res["code"] == 0
    assert res["data"]["id"] == "dataset-2"

    def _raise_get(_dataset_id):
        raise RuntimeError("get dataset boom")

    monkeypatch.setattr(module.EvaluationService, "get_dataset", _raise_get)
    res = _run(module.get_dataset("dataset-3"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "get dataset boom" in res["message"]

    captured = {}

    def _update(dataset_id, **kwargs):
        captured["dataset_id"] = dataset_id
        captured["kwargs"] = kwargs
        return True

    _set_request_json(
        monkeypatch,
        module,
        {
            "id": "forbidden",
            "tenant_id": "forbidden",
            "created_by": "forbidden",
            "create_time": 123,
            "name": "new-name",
        },
    )
    monkeypatch.setattr(module.EvaluationService, "update_dataset", _update)
    res = _run(module.update_dataset("dataset-4"))
    assert res["code"] == 0
    assert res["data"]["dataset_id"] == "dataset-4"
    assert captured["dataset_id"] == "dataset-4"
    assert "id" not in captured["kwargs"]
    assert "tenant_id" not in captured["kwargs"]
    assert "created_by" not in captured["kwargs"]
    assert "create_time" not in captured["kwargs"]

    _set_request_json(monkeypatch, module, {"name": "new-name"})
    monkeypatch.setattr(module.EvaluationService, "update_dataset", lambda _dataset_id, **_kwargs: False)
    res = _run(module.update_dataset("dataset-5"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "failed" in res["message"].lower()

    def _raise_update(_dataset_id, **_kwargs):
        raise RuntimeError("update boom")

    monkeypatch.setattr(module.EvaluationService, "update_dataset", _raise_update)
    res = _run(module.update_dataset("dataset-6"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "update boom" in res["message"]

    monkeypatch.setattr(module.EvaluationService, "delete_dataset", lambda _dataset_id: False)
    res = _run(module.delete_dataset("dataset-7"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "failed" in res["message"].lower()

    monkeypatch.setattr(module.EvaluationService, "delete_dataset", lambda _dataset_id: True)
    res = _run(module.delete_dataset("dataset-8"))
    assert res["code"] == 0
    assert res["data"]["dataset_id"] == "dataset-8"

    def _raise_delete(_dataset_id):
        raise RuntimeError("delete dataset boom")

    monkeypatch.setattr(module.EvaluationService, "delete_dataset", _raise_delete)
    res = _run(module.delete_dataset("dataset-9"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "delete dataset boom" in res["message"]