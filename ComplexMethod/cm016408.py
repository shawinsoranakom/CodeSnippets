def test_list_assets_paging_and_sort(http: requests.Session, api_base: str, asset_factory, make_asset_bytes):
    names = ["a1_u.safetensors", "a2_u.safetensors", "a3_u.safetensors"]
    for n in names:
        asset_factory(
            n,
            ["models", "checkpoints", "unit-tests", "paging"],
            {"epoch": 1},
            make_asset_bytes(n, size=2048),
        )

    # name ascending for stable order
    r1 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,paging", "sort": "name", "order": "asc", "limit": "2", "offset": "0"},
        timeout=120,
    )
    b1 = r1.json()
    assert r1.status_code == 200
    got1 = [a["name"] for a in b1["assets"]]
    assert got1 == sorted(names)[:2]
    assert b1["has_more"] is True

    r2 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,paging", "sort": "name", "order": "asc", "limit": "2", "offset": "2"},
        timeout=120,
    )
    b2 = r2.json()
    assert r2.status_code == 200
    got2 = [a["name"] for a in b2["assets"]]
    assert got2 == sorted(names)[2:]
    assert b2["has_more"] is False