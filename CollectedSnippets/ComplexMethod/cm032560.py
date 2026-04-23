def test_agree_success_and_exception_unit(monkeypatch):
    module = _load_tenant_module(monkeypatch)

    calls = []
    monkeypatch.setattr(module.UserTenantService, "filter_update", lambda conditions, payload: calls.append((conditions, payload)) or True)
    res = module.agree("tenant-1")
    assert res["code"] == 0, res
    assert res["data"] is True, res
    assert calls and calls[-1][1]["role"] == module.UserTenantRole.NORMAL

    monkeypatch.setattr(module.UserTenantService, "filter_update", lambda _conditions, _payload: (_ for _ in ()).throw(RuntimeError("agree boom")))
    res = module.agree("tenant-1")
    assert res["code"] == 100, res
    assert "agree boom" in res["message"], res