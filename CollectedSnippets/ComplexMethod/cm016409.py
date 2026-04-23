def test_list_assets_include_exclude_and_name_contains(http: requests.Session, api_base: str, asset_factory):
    a = asset_factory("inc_a.safetensors", ["models", "checkpoints", "unit-tests", "alpha"], {}, b"X" * 1024)
    b = asset_factory("inc_b.safetensors", ["models", "checkpoints", "unit-tests", "beta"], {}, b"Y" * 1024)

    r = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,alpha", "exclude_tags": "beta", "limit": "50"},
        timeout=120,
    )
    body = r.json()
    assert r.status_code == 200
    names = [x["name"] for x in body["assets"]]
    assert a["name"] in names
    assert b["name"] not in names

    r2 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests", "name_contains": "inc_"},
        timeout=120,
    )
    body2 = r2.json()
    assert r2.status_code == 200
    names2 = [x["name"] for x in body2["assets"]]
    assert a["name"] in names2
    assert b["name"] in names2

    r2 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "non-existing-tag"},
        timeout=120,
    )
    body3 = r2.json()
    assert r2.status_code == 200
    assert not body3["assets"]