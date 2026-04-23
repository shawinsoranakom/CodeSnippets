def test_rm_and_tenant_list_matrix_unit(monkeypatch):
    module = _load_tenant_module(monkeypatch)

    module.current_user.id = "outsider"
    _set_request_json(monkeypatch, module, {"user_id": "user-2"})
    res = _run(module.rm("tenant-1"))
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res
    assert res["message"] == "No authorization.", res

    module.current_user.id = "tenant-1"
    deleted = []
    monkeypatch.setattr(module.UserTenantService, "filter_delete", lambda conditions: deleted.append(conditions) or True)
    res = _run(module.rm("tenant-1"))
    assert res["code"] == 0, res
    assert res["data"] is True, res
    assert deleted, "filter_delete should be called"

    monkeypatch.setattr(module.UserTenantService, "filter_delete", lambda _conditions: (_ for _ in ()).throw(RuntimeError("rm boom")))
    res = _run(module.rm("tenant-1"))
    assert res["code"] == 100, res
    assert "rm boom" in res["message"], res

    monkeypatch.setattr(
        module.UserTenantService,
        "get_tenants_by_user_id",
        lambda _user_id: [{"id": "tenant-1", "update_date": "2024-01-01 00:00:00"}],
    )
    monkeypatch.setattr(module, "delta_seconds", lambda _value: 9)
    res = module.tenant_list()
    assert res["code"] == 0, res
    assert res["data"][0]["delta_seconds"] == 9, res

    monkeypatch.setattr(module.UserTenantService, "get_tenants_by_user_id", lambda _user_id: (_ for _ in ()).throw(RuntimeError("tenant boom")))
    res = module.tenant_list()
    assert res["code"] == 100, res
    assert "tenant boom" in res["message"], res