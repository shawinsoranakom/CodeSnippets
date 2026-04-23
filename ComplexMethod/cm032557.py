def test_user_list_auth_success_exception_matrix_unit(monkeypatch):
    module = _load_tenant_module(monkeypatch)

    module.current_user.id = "other-user"
    res = module.user_list("tenant-1")
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res
    assert res["message"] == "No authorization.", res

    module.current_user.id = "tenant-1"
    monkeypatch.setattr(
        module.UserTenantService,
        "get_by_tenant_id",
        lambda _tenant_id: [{"id": "u1", "update_date": "2024-01-01 00:00:00"}],
    )
    monkeypatch.setattr(module, "delta_seconds", lambda _value: 42)
    res = module.user_list("tenant-1")
    assert res["code"] == 0, res
    assert res["data"][0]["delta_seconds"] == 42, res

    monkeypatch.setattr(module.UserTenantService, "get_by_tenant_id", lambda _tenant_id: (_ for _ in ()).throw(RuntimeError("list boom")))
    res = module.user_list("tenant-1")
    assert res["code"] == 100, res
    assert "list boom" in res["message"], res