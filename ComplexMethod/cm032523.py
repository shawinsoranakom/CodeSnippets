def test_list_chats_returns_old_business_fields(monkeypatch):
    module = _load_chat_module(monkeypatch)
    monkeypatch.setattr(
        module,
        "request",
        SimpleNamespace(
            args=SimpleNamespace(
                get=lambda key, default=None: {
                    "keywords": "",
                    "page": 1,
                    "page_size": 20,
                    "orderby": "create_time",
                    "desc": "true",
                }.get(key, default),
                getlist=lambda _key: [],
            )
        ),
    )
    monkeypatch.setattr(
        module.DialogService,
        "get_by_tenant_ids",
        lambda *_args, **_kwargs: (
            [_DummyDialogRecord().to_dict()],
            1,
        ),
    )
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _id: (True, _DummyKB()))

    res = module.list_chats.__wrapped__()

    assert res["code"] == 0
    chat = res["data"]["chats"][0]
    assert chat["icon"] == "icon.png"
    assert chat["dataset_ids"] == ["kb-1"]
    assert chat["kb_names"] == ["Dataset A"]
    assert "kb_ids" not in chat
    assert chat["prompt_config"]["prologue"] == "hello"
    assert "dataset_names" not in chat
    assert "prompt" not in chat
    assert "llm" not in chat