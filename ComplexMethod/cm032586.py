def test_status_branch_matrix_unit(monkeypatch):
    module = _load_system_module(monkeypatch)

    monkeypatch.setattr(module.settings, "docStoreConn", SimpleNamespace(health=lambda: {"type": "es", "status": "green"}))
    monkeypatch.setattr(module.settings, "STORAGE_IMPL", SimpleNamespace(health=lambda: True))
    monkeypatch.setattr(module.KnowledgebaseService, "get_by_id", lambda _kb_id: True)
    monkeypatch.setattr(module.REDIS_CONN, "health", lambda: True)
    monkeypatch.setattr(module.REDIS_CONN, "smembers", lambda _key: {"executor-1"})
    monkeypatch.setattr(module.REDIS_CONN, "zrangebyscore", lambda *_args, **_kwargs: ['{"beat": 1}'])

    res = module.status()
    assert res["code"] == 0
    assert res["data"]["doc_engine"]["status"] == "green"
    assert res["data"]["storage"]["status"] == "green"
    assert res["data"]["database"]["status"] == "green"
    assert res["data"]["redis"]["status"] == "green"
    assert res["data"]["task_executor_heartbeats"]["executor-1"][0]["beat"] == 1

    monkeypatch.setattr(
        module.settings,
        "docStoreConn",
        SimpleNamespace(health=lambda: (_ for _ in ()).throw(RuntimeError("doc down"))),
    )
    monkeypatch.setattr(
        module.settings,
        "STORAGE_IMPL",
        SimpleNamespace(health=lambda: (_ for _ in ()).throw(RuntimeError("storage down"))),
    )
    monkeypatch.setattr(
        module.KnowledgebaseService,
        "get_by_id",
        lambda _kb_id: (_ for _ in ()).throw(RuntimeError("db down")),
    )
    monkeypatch.setattr(module.REDIS_CONN, "health", lambda: False)
    monkeypatch.setattr(module.REDIS_CONN, "smembers", lambda _key: (_ for _ in ()).throw(RuntimeError("hb down")))

    res = module.status()
    assert res["code"] == 0
    assert res["data"]["doc_engine"]["status"] == "red"
    assert "doc down" in res["data"]["doc_engine"]["error"]
    assert res["data"]["storage"]["status"] == "red"
    assert "storage down" in res["data"]["storage"]["error"]
    assert res["data"]["database"]["status"] == "red"
    assert "db down" in res["data"]["database"]["error"]
    assert res["data"]["redis"]["status"] == "red"
    assert "Lost connection!" in res["data"]["redis"]["error"]
    assert res["data"]["task_executor_heartbeats"] == {}