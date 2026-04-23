def test_create_chat_uses_direct_chat_fields(monkeypatch):
    module = _load_chat_module(monkeypatch)
    saved = {}

    _set_request_json(
        monkeypatch,
        module,
        {
            "name": "chat-a",
            "icon": "icon.png",
            "dataset_ids": ["kb-1"],
            "llm_id": "glm-4",
            "llm_setting": {"temperature": 0.8},
            "prompt_config": {
                "system": "Answer with {knowledge}",
                "parameters": [{"key": "knowledge", "optional": False}],
                "prologue": "Hi",
            },
            "vector_similarity_weight": 0.25,
        },
    )
    monkeypatch.setattr(module.TenantService, "get_by_id", lambda _tid: (True, SimpleNamespace(llm_id="glm-4")))
    monkeypatch.setattr(module.DialogService, "query", lambda **_kwargs: [])
    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda **_kwargs: [SimpleNamespace(id="kb-1")])
    monkeypatch.setattr(module.KnowledgebaseService, "query", lambda **_kwargs: [_DummyKB()])
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _id: (True, _DummyKB()))
    monkeypatch.setattr(module.TenantLLMService, "split_model_name_and_factory", lambda model: (model.split("@")[0], "factory"))
    monkeypatch.setattr(module.TenantLLMService, "query", lambda **_kwargs: [SimpleNamespace(id="llm-1")])

    def _save(**kwargs):
        saved.update(kwargs)
        return True

    monkeypatch.setattr(module.DialogService, "save", _save)
    monkeypatch.setattr(module.DialogService, "get_by_id", lambda _id: (True, _DummyDialogRecord(saved)))

    res = _run(module.create.__wrapped__())

    assert res["code"] == 0
    assert saved["kb_ids"] == ["kb-1"]
    assert saved["prompt_config"]["prologue"] == "Hi"
    assert saved["llm_id"] == "glm-4"
    assert saved["llm_setting"]["temperature"] == 0.8
    assert res["data"]["dataset_ids"] == ["kb-1"]
    assert res["data"]["kb_names"] == ["Dataset A"]
    assert "kb_ids" not in res["data"]
    assert "prompt" not in res["data"]
    assert "llm" not in res["data"]
    assert "avatar" not in res["data"]