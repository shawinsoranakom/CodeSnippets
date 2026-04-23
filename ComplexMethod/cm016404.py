def test_meta_sort_and_paging_under_filter(http, api_base, asset_factory, make_asset_bytes):
    # Three assets in same scope with different sizes and a common filter key
    t = ["models", "checkpoints", "unit-tests", "mf-sort"]
    n1, n2, n3 = "mf_sort_1.safetensors", "mf_sort_2.safetensors", "mf_sort_3.safetensors"
    asset_factory(n1, t, {"group": "g"}, make_asset_bytes(n1, 1024))
    asset_factory(n2, t, {"group": "g"}, make_asset_bytes(n2, 2048))
    asset_factory(n3, t, {"group": "g"}, make_asset_bytes(n3, 3072))

    # Sort by size ascending with paging
    q = {
        "include_tags": "unit-tests,mf-sort",
        "metadata_filter": json.dumps({"group": "g"}),
        "sort": "size", "order": "asc", "limit": "2",
    }
    r1 = http.get(api_base + "/api/assets", params=q, timeout=120)
    b1 = r1.json()
    assert r1.status_code == 200
    got1 = [a["name"] for a in b1["assets"]]
    assert got1 == [n1, n2]
    assert b1["has_more"] is True

    q2 = {**q, "offset": "2"}
    r2 = http.get(api_base + "/api/assets", params=q2, timeout=120)
    b2 = r2.json()
    assert r2.status_code == 200
    got2 = [a["name"] for a in b2["assets"]]
    assert got2 == [n3]
    assert b2["has_more"] is False