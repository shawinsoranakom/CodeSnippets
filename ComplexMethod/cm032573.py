def test_list_and_delete_route_matrix_unit(monkeypatch):
    module = _load_search_api(monkeypatch)

    # list: no owner_ids, with pagination
    _set_request_args(
        monkeypatch,
        module,
        {"keywords": "k", "page": "1", "page_size": "2", "orderby": "create_time", "desc": "false"},
    )
    monkeypatch.setattr(
        module.SearchService,
        "get_by_tenant_ids",
        lambda _tenants, _uid, _page, _size, _orderby, _desc, _keywords: ([{"id": "a", "tenant_id": "tenant-1"}], 1),
    )
    res = module.list_searches()
    assert res["code"] == 0
    assert res["data"]["total"] == 1
    assert res["data"]["search_apps"][0]["id"] == "a"

    # list: with owner_ids filter and pagination
    _set_request_args(
        monkeypatch,
        module,
        {"keywords": "k", "page": "1", "page_size": "1", "orderby": "create_time", "desc": "true", "owner_ids": ["tenant-1"]},
    )
    monkeypatch.setattr(
        module.SearchService,
        "get_by_tenant_ids",
        lambda _tenants, _uid, _page, _size, _orderby, _desc, _keywords: (
            [{"id": "x", "tenant_id": "tenant-1"}, {"id": "y", "tenant_id": "tenant-2"}],
            2,
        ),
    )
    res = module.list_searches()
    assert res["code"] == 0
    assert res["data"]["total"] == 1
    assert len(res["data"]["search_apps"]) == 1
    assert res["data"]["search_apps"][0]["tenant_id"] == "tenant-1"

    # list: exception
    def _raise_list(*_args, **_kwargs):
        raise RuntimeError("list boom")

    monkeypatch.setattr(module.SearchService, "get_by_tenant_ids", _raise_list)
    _set_request_args(monkeypatch, module, {})
    res = module.list_searches()
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "list boom" in res["message"]

    # delete: no authorization
    monkeypatch.setattr(module.SearchService, "accessible4deletion", lambda _search_id, _user_id: False)
    res = module.delete_search(search_id="search-1")
    assert res["code"] == module.RetCode.AUTHENTICATION_ERROR
    assert "authorization" in res["message"].lower()

    # delete: delete_by_id fails
    monkeypatch.setattr(module.SearchService, "accessible4deletion", lambda _search_id, _user_id: True)
    monkeypatch.setattr(module.SearchService, "delete_by_id", lambda _search_id: False)
    res = module.delete_search(search_id="search-1")
    assert res["code"] == module.RetCode.DATA_ERROR
    assert "failed to delete" in res["message"].lower()

    # delete: success
    monkeypatch.setattr(module.SearchService, "delete_by_id", lambda _search_id: True)
    res = module.delete_search(search_id="search-1")
    assert res["code"] == 0
    assert res["data"] is True

    # delete: exception
    def _raise_delete(_search_id):
        raise RuntimeError("rm boom")

    monkeypatch.setattr(module.SearchService, "delete_by_id", _raise_delete)
    res = module.delete_search(search_id="search-1")
    assert res["code"] == module.RetCode.EXCEPTION_ERROR
    assert "rm boom" in res["message"]