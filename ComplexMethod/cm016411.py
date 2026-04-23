def test_list_assets_name_contains_case_and_specials(http, api_base, asset_factory, make_asset_bytes):
    t = ["models", "checkpoints", "unit-tests", "lf-name"]
    a1 = asset_factory("CaseMix.SAFE", t, {}, make_asset_bytes("cm", 800))
    a2 = asset_factory("case-other.safetensors", t, {}, make_asset_bytes("co", 800))

    r1 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,lf-name", "name_contains": "casemix"},
        timeout=120,
    )
    b1 = r1.json()
    assert r1.status_code == 200
    names1 = [x["name"] for x in b1["assets"]]
    assert a1["name"] in names1

    r2 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,lf-name", "name_contains": ".SAFE"},
        timeout=120,
    )
    b2 = r2.json()
    assert r2.status_code == 200
    names2 = [x["name"] for x in b2["assets"]]
    assert a1["name"] in names2

    r3 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,lf-name", "name_contains": "case-"},
        timeout=120,
    )
    b3 = r3.json()
    assert r3.status_code == 200
    names3 = [x["name"] for x in b3["assets"]]
    assert a2["name"] in names3