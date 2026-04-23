def test_tags_list_order_and_prefix(http: requests.Session, api_base: str, seeded_asset: dict):
    aid = seeded_asset["id"]
    h = seeded_asset["asset_hash"]

    # Add both tags to the seeded asset (usage: orderaaa=1, orderbbb=1)
    r_add = http.post(f"{api_base}/api/assets/{aid}/tags", json={"tags": ["orderaaa", "orderbbb"]}, timeout=120)
    add_body = r_add.json()
    assert r_add.status_code == 200, add_body

    # Create another AssetInfo from the same content but tagged ONLY with 'orderbbb'.
    payload = {
        "hash": h,
        "name": "order_only_bbb.safetensors",
        "tags": ["input", "unit-tests", "orderbbb"],
        "user_metadata": {},
    }
    r_copy = http.post(f"{api_base}/api/assets/from-hash", json=payload, timeout=120)
    copy_body = r_copy.json()
    assert r_copy.status_code == 201, copy_body

    # 1) Default order (count_desc): 'orderbbb' should come before 'orderaaa'
    #    because it has higher usage (2 vs 1).
    r1 = http.get(api_base + "/api/tags", params={"prefix": "order", "include_zero": "false"}, timeout=120)
    b1 = r1.json()
    assert r1.status_code == 200, b1
    names1 = [t["name"] for t in b1["tags"]]
    counts1 = {t["name"]: t["count"] for t in b1["tags"]}
    # Both must be present within the prefix subset
    assert "orderaaa" in names1 and "orderbbb" in names1
    # Usage of 'orderbbb' must be >= 'orderaaa'; in our setup it's 2 vs 1
    assert counts1["orderbbb"] >= counts1["orderaaa"]
    # And with count_desc, 'orderbbb' appears earlier than 'orderaaa'
    assert names1.index("orderbbb") < names1.index("orderaaa")

    # 2) name_asc: lexical order should flip the relative order
    r2 = http.get(
        api_base + "/api/tags",
        params={"prefix": "order", "include_zero": "false", "order": "name_asc"},
        timeout=120,
    )
    b2 = r2.json()
    assert r2.status_code == 200, b2
    names2 = [t["name"] for t in b2["tags"]]
    assert "orderaaa" in names2 and "orderbbb" in names2
    assert names2.index("orderaaa") < names2.index("orderbbb")

    # 3) invalid limit rejected (existing negative case retained)
    r3 = http.get(api_base + "/api/tags", params={"limit": "1001"}, timeout=120)
    b3 = r3.json()
    assert r3.status_code == 400
    assert b3["error"]["code"] == "INVALID_QUERY"