def test_list_knowledge_graph_delete_kg_matrix_unit(monkeypatch):
    module = _load_dataset_module(monkeypatch)

    _set_request_args(monkeypatch, module, {"id": "", "name": "", "page": 1, "page_size": 30, "orderby": "create_time", "desc": True})
    monkeypatch.setattr(
        module,
        "validate_and_parse_request_args",
        lambda *_args, **_kwargs: ({"name": "", "page": 1, "page_size": 30, "orderby": "create_time", "desc": True}, None),
    )
    monkeypatch.setattr(
        module.KnowledgebaseService,
        "get_list",
        lambda *_args, **_kwargs: (_ for _ in ()).throw(module.OperationalError("list down")),
    )
    res = module.list_datasets("tenant-1")
    assert res["code"] == module.RetCode.DATA_ERROR, res
    assert res["message"] == "Database operation failed", res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = _run(inspect.unwrap(module.knowledge_graph)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: True)
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: (True, _KB(tenant_id="tenant-1")))
    monkeypatch.setattr(module.search, "index_name", lambda _tenant_id: "idx")
    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(index_exist=lambda *_args, **_kwargs: False))
    res = _run(inspect.unwrap(module.knowledge_graph)("tenant-1", "kb-1"))
    assert res["data"] == {"graph": {}, "mind_map": {}}, res

    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(index_exist=lambda *_args, **_kwargs: True))

    class _EmptyRetriever:
        async def search(self, *_args, **_kwargs):
            return SimpleNamespace(ids=[], field={})

    monkeypatch.setattr(module.settings, "retriever", _EmptyRetriever())
    res = _run(inspect.unwrap(module.knowledge_graph)("tenant-1", "kb-1"))
    assert res["data"] == {"graph": {}, "mind_map": {}}, res

    class _BadRetriever:
        async def search(self, *_args, **_kwargs):
            return SimpleNamespace(ids=["bad"], field={"bad": {"knowledge_graph_kwd": "graph", "content_with_weight": "{bad"}})

    monkeypatch.setattr(module.settings, "retriever", _BadRetriever())
    res = _run(inspect.unwrap(module.knowledge_graph)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert res["data"]["graph"] == {}, res

    payload = {
        "nodes": [{"id": "n2", "pagerank": 2}, {"id": "n1", "pagerank": 5}],
        "edges": [
            {"source": "n1", "target": "n2", "weight": 2},
            {"source": "n1", "target": "n1", "weight": 10},
            {"source": "n1", "target": "n3", "weight": 9},
        ],
    }

    class _GoodRetriever:
        async def search(self, *_args, **_kwargs):
            return SimpleNamespace(ids=["good"], field={"good": {"knowledge_graph_kwd": "graph", "content_with_weight": json.dumps(payload)}})

    monkeypatch.setattr(module.settings, "retriever", _GoodRetriever())
    res = _run(inspect.unwrap(module.knowledge_graph)("tenant-1", "kb-1"))
    assert res["code"] == module.RetCode.SUCCESS, res
    assert len(res["data"]["graph"]["nodes"]) == 2, res
    assert len(res["data"]["graph"]["edges"]) == 1, res

    monkeypatch.setattr(module.KnowledgebaseService, "accessible", lambda *_args, **_kwargs: False)
    res = inspect.unwrap(module.delete_knowledge_graph)("tenant-1", "kb-1")
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res