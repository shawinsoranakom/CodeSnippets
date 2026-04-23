def test_registration_helpers_and_register_route_matrix_unit(monkeypatch):
    module = _load_user_app(monkeypatch)

    deleted = {"user": 0, "tenant": 0, "user_tenant": 0, "tenant_llm": 0}
    monkeypatch.setattr(module.UserService, "delete_by_id", lambda _user_id: deleted.__setitem__("user", deleted["user"] + 1))
    monkeypatch.setattr(module.TenantService, "delete_by_id", lambda _tenant_id: deleted.__setitem__("tenant", deleted["tenant"] + 1))
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(id="ut-1")])
    monkeypatch.setattr(module.UserTenantService, "delete_by_id", lambda _ut_id: deleted.__setitem__("user_tenant", deleted["user_tenant"] + 1))

    class _DeleteQuery:
        def where(self, *_args, **_kwargs):
            return self

        def execute(self):
            deleted["tenant_llm"] += 1
            return 1

    monkeypatch.setattr(module.TenantLLM, "delete", lambda: _DeleteQuery())
    module.rollback_user_registration("user-1")
    assert deleted == {"user": 1, "tenant": 1, "user_tenant": 1, "tenant_llm": 1}, deleted

    monkeypatch.setattr(module.UserService, "delete_by_id", lambda _user_id: (_ for _ in ()).throw(RuntimeError("u boom")))
    monkeypatch.setattr(module.TenantService, "delete_by_id", lambda _tenant_id: (_ for _ in ()).throw(RuntimeError("t boom")))
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: (_ for _ in ()).throw(RuntimeError("ut boom")))

    class _RaisingDeleteQuery:
        def where(self, *_args, **_kwargs):
            raise RuntimeError("llm boom")

    monkeypatch.setattr(module.TenantLLM, "delete", lambda: _RaisingDeleteQuery())
    module.rollback_user_registration("user-2")

    monkeypatch.setattr(module.UserService, "save", lambda **_kwargs: False)
    res = module.user_register(
        "new-user",
        {
            "nickname": "new",
            "email": "new@example.com",
            "password": "pw",
            "access_token": "tk",
            "login_channel": "password",
            "last_login_time": "2024-01-01 00:00:00",
            "is_superuser": False,
        },
    )
    assert res is None

    monkeypatch.setattr(module.settings, "REGISTER_ENABLED", False)
    _set_request_json(monkeypatch, module, {"nickname": "neo", "email": "neo@example.com", "password": "enc"})
    res = _run(module.user_add())
    assert res["code"] == module.RetCode.OPERATING_ERROR, res
    assert "disabled" in res["message"], res

    monkeypatch.setattr(module.settings, "REGISTER_ENABLED", True)
    _set_request_json(monkeypatch, module, {"nickname": "neo", "email": "bad-email", "password": "enc"})
    res = _run(module.user_add())
    assert res["code"] == module.RetCode.OPERATING_ERROR, res
    assert "Invalid email address" in res["message"], res

    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    monkeypatch.setattr(module, "decrypt", lambda value: value)
    monkeypatch.setattr(module, "get_uuid", lambda: "new-user-id")
    rollback_calls = []
    monkeypatch.setattr(module, "rollback_user_registration", lambda user_id: rollback_calls.append(user_id))

    _set_request_json(monkeypatch, module, {"nickname": "neo", "email": "neo@example.com", "password": "enc"})
    monkeypatch.setattr(module, "user_register", lambda _user_id, _payload: None)
    res = _run(module.user_add())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "Fail to register neo@example.com." in res["message"], res
    assert rollback_calls == ["new-user-id"], rollback_calls

    rollback_calls.clear()
    monkeypatch.setattr(
        module,
        "user_register",
        lambda _user_id, _payload: [_DummyUser("dup-1", "neo@example.com"), _DummyUser("dup-2", "neo@example.com")],
    )
    _set_request_json(monkeypatch, module, {"nickname": "neo", "email": "neo@example.com", "password": "enc"})
    res = _run(module.user_add())
    assert res["code"] == module.RetCode.EXCEPTION_ERROR, res
    assert "Same email: neo@example.com exists!" in res["message"], res
    assert rollback_calls == ["new-user-id"], rollback_calls