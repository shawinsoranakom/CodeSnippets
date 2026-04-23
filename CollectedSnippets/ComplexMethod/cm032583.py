def test_test_case_routes_matrix_unit(monkeypatch):
    module = _load_evaluation_app(monkeypatch)

    _set_request_json(monkeypatch, module, {"question": "   "})
    res = _run(module.add_test_case("dataset-1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "question" in res["message"].lower()

    _set_request_json(monkeypatch, module, {"question": "q1"})
    monkeypatch.setattr(module.EvaluationService, "add_test_case", lambda **_kwargs: (False, "add failed"))
    res = _run(module.add_test_case("dataset-2"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "add failed" in res["message"]

    _set_request_json(
        monkeypatch,
        module,
        {
            "question": "q2",
            "reference_answer": "a2",
            "relevant_doc_ids": ["doc-1"],
            "relevant_chunk_ids": ["chunk-1"],
            "metadata": {"k": "v"},
        },
    )
    monkeypatch.setattr(module.EvaluationService, "add_test_case", lambda **_kwargs: (True, "case-ok"))
    res = _run(module.add_test_case("dataset-3"))
    assert res["code"] == 0
    assert res["data"]["case_id"] == "case-ok"

    def _raise_add(**_kwargs):
        raise RuntimeError("add case boom")

    monkeypatch.setattr(module.EvaluationService, "add_test_case", _raise_add)
    res = _run(module.add_test_case("dataset-4"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "add case boom" in res["message"]

    _set_request_json(monkeypatch, module, {"cases": {}})
    res = _run(module.import_test_cases("dataset-5"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "cases" in res["message"]

    _set_request_json(monkeypatch, module, {"cases": [{"question": "q1"}, {"question": "q2"}]})
    monkeypatch.setattr(module.EvaluationService, "import_test_cases", lambda **_kwargs: (2, 0))
    res = _run(module.import_test_cases("dataset-6"))
    assert res["code"] == 0
    assert res["data"]["success_count"] == 2
    assert res["data"]["failure_count"] == 0
    assert res["data"]["total"] == 2

    def _raise_import(**_kwargs):
        raise RuntimeError("import boom")

    monkeypatch.setattr(module.EvaluationService, "import_test_cases", _raise_import)
    res = _run(module.import_test_cases("dataset-7"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "import boom" in res["message"]

    monkeypatch.setattr(module.EvaluationService, "get_test_cases", lambda _dataset_id: [{"id": "case-1"}])
    res = _run(module.get_test_cases("dataset-8"))
    assert res["code"] == 0
    assert res["data"]["total"] == 1
    assert res["data"]["cases"][0]["id"] == "case-1"

    def _raise_get_cases(_dataset_id):
        raise RuntimeError("get cases boom")

    monkeypatch.setattr(module.EvaluationService, "get_test_cases", _raise_get_cases)
    res = _run(module.get_test_cases("dataset-9"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "get cases boom" in res["message"]

    monkeypatch.setattr(module.EvaluationService, "delete_test_case", lambda _case_id: False)
    res = _run(module.delete_test_case("case-1"))
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "failed" in res["message"].lower()

    monkeypatch.setattr(module.EvaluationService, "delete_test_case", lambda _case_id: True)
    res = _run(module.delete_test_case("case-2"))
    assert res["code"] == 0
    assert res["data"]["case_id"] == "case-2"

    def _raise_delete_case(_case_id):
        raise RuntimeError("delete case boom")

    monkeypatch.setattr(module.EvaluationService, "delete_test_case", _raise_delete_case)
    res = _run(module.delete_test_case("case-3"))
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "delete case boom" in res["message"]