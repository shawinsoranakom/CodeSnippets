def test_connector_basic_routes_and_task_controls(monkeypatch):
    module = _load_connector_app(monkeypatch)

    async def _no_sleep(_secs):
        return None

    monkeypatch.setattr(module.asyncio, "sleep", _no_sleep)

    records = {"conn-1": _FakeConnectorRecord({"id": "conn-1", "source": "drive"})}
    update_calls = []
    save_calls = []
    resume_calls = []
    delete_calls = []

    monkeypatch.setattr(module.ConnectorService, "update_by_id", lambda cid, payload: update_calls.append((cid, payload)))

    def _save(**payload):
        save_calls.append(payload)
        records[payload["id"]] = _FakeConnectorRecord(payload)

    monkeypatch.setattr(module.ConnectorService, "save", _save)
    monkeypatch.setattr(module.ConnectorService, "get_by_id", lambda cid: (True, records[cid]))
    monkeypatch.setattr(module.ConnectorService, "list", lambda tenant_id: [{"id": "listed", "tenant": tenant_id}])
    monkeypatch.setattr(module.SyncLogsService, "list_sync_tasks", lambda cid, page, page_size: ([{"id": "log-1"}], 9))
    monkeypatch.setattr(module.ConnectorService, "resume", lambda cid, status: resume_calls.append((cid, status)))
    monkeypatch.setattr(module.ConnectorService, "delete_by_id", lambda cid: delete_calls.append(cid))
    monkeypatch.setattr(module, "get_uuid", lambda: "generated-id")

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"id": "conn-1", "refresh_freq": 7, "config": {"x": 1}}),
    )
    res = _run(module.update_connector("conn-1"))
    assert update_calls == [("conn-1", {'id': 'conn-1', "refresh_freq": 7, "config": {"x": 1}})]
    assert res["data"]["id"] == "conn-1"

    monkeypatch.setattr(
        module,
        "get_request_json",
        lambda: _AwaitableValue({"name": "new", "source": "gmail", "config": {"y": 2}}),
    )
    res = _run(module.create_connector())
    assert save_calls[-1]["id"] == "generated-id"
    assert save_calls[-1]["tenant_id"] == "tenant-1"
    assert save_calls[-1]["input_type"] == module.InputType.POLL
    assert res["data"]["id"] == "generated-id"

    list_res = module.list_connector()
    assert list_res["data"] == [{"id": "listed", "tenant": "tenant-1"}]

    monkeypatch.setattr(module.ConnectorService, "get_by_id", lambda _cid: (False, None))
    missing_res = module.get_connector("missing")
    assert missing_res["message"] == "Can't find this Connector!"

    monkeypatch.setattr(module.ConnectorService, "get_by_id", lambda cid: (True, _FakeConnectorRecord({"id": cid})))
    found_res = module.get_connector("conn-2")
    assert found_res["data"]["id"] == "conn-2"

    _set_request(module, args={"page": "2", "page_size": "7"})
    logs_res = module.list_logs("conn-log")
    assert logs_res["data"] == {"total": 9, "logs": [{"id": "log-1"}]}

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"resume": True}))
    assert _run(module.resume("conn-r1"))["data"] is True

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"resume": False}))
    assert _run(module.resume("conn-r2"))["data"] is True
    assert ("conn-r1", module.TaskStatus.SCHEDULE) in resume_calls
    assert ("conn-r2", module.TaskStatus.CANCEL) in resume_calls

    monkeypatch.setattr(module, "get_request_json", lambda: _AwaitableValue({"kb_id": "kb-1"}))
    monkeypatch.setattr(module.ConnectorService, "rebuild", lambda *_args: "rebuild-failed")
    failed_rebuild = _run(module.rebuild("conn-rb"))
    assert failed_rebuild["code"] == module.RetCode.SERVER_ERROR
    assert failed_rebuild["data"] is False

    monkeypatch.setattr(module.ConnectorService, "rebuild", lambda *_args: None)
    ok_rebuild = _run(module.rebuild("conn-rb"))
    assert ok_rebuild["data"] is True

    rm_res = module.rm_connector("conn-rm")
    assert rm_res["data"] is True
    assert ("conn-rm", module.TaskStatus.CANCEL) in resume_calls
    assert delete_calls == ["conn-rm"]