def test_create_invite_role_and_email_failure_matrix_unit(monkeypatch):
    module = _load_tenant_module(monkeypatch)

    module.current_user.id = "other-user"
    _set_request_json(monkeypatch, module, {"email": "invitee@example.com"})
    res = _run(module.create("tenant-1"))
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR, res
    assert res["message"] == "No authorization.", res

    module.current_user.id = "tenant-1"
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [])
    res = _run(module.create("tenant-1"))
    assert res["message"] == "User not found.", res

    invitee = _Invitee()
    monkeypatch.setattr(module.UserService, "query", lambda **_kwargs: [invitee])
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(role=module.UserTenantRole.NORMAL)])
    res = _run(module.create("tenant-1"))
    assert "already in the team." in res["message"], res

    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(role=module.UserTenantRole.OWNER)])
    res = _run(module.create("tenant-1"))
    assert "owner of the team." in res["message"], res

    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [SimpleNamespace(role="strange-role")])
    res = _run(module.create("tenant-1"))
    assert "role: strange-role is invalid." in res["message"], res

    saved = []
    scheduled = []
    monkeypatch.setattr(module.UserTenantService, "query", lambda **_kwargs: [])
    monkeypatch.setattr(module.UserTenantService, "save", lambda **kwargs: saved.append(kwargs) or True)
    monkeypatch.setattr(module.UserService, "get_by_id", lambda _user_id: (True, SimpleNamespace(nickname="Inviter Nick")))
    monkeypatch.setattr(module, "send_invite_email", lambda **kwargs: kwargs)
    monkeypatch.setattr(module.asyncio, "create_task", lambda payload: scheduled.append(payload) or SimpleNamespace())
    res = _run(module.create("tenant-1"))
    assert res["code"] == 0, res
    assert saved and saved[-1]["role"] == module.UserTenantRole.INVITE, saved
    assert scheduled and scheduled[-1]["inviter"] == "Inviter Nick", scheduled
    assert sorted(res["data"].keys()) == ["avatar", "email", "id", "nickname"], res

    monkeypatch.setattr(module.asyncio, "create_task", lambda _payload: (_ for _ in ()).throw(RuntimeError("send boom")))
    res = _run(module.create("tenant-1"))
    assert res["code"] == module.RetCode.SERVER_ERROR, res
    assert "Failed to send invite email." in res["message"], res