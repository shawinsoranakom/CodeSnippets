def test_tags_present(http: requests.Session, api_base: str, seeded_asset: dict):
    # Include zero-usage tags by default
    r1 = http.get(api_base + "/api/tags", params={"limit": "50"}, timeout=120)
    body1 = r1.json()
    assert r1.status_code == 200
    names = [t["name"] for t in body1["tags"]]
    # A few system tags from migration should exist:
    assert "models" in names
    assert "checkpoints" in names

    # Only used tags before we add anything new from this test cycle
    r2 = http.get(api_base + "/api/tags", params={"include_zero": "false"}, timeout=120)
    body2 = r2.json()
    assert r2.status_code == 200
    # We already seeded one asset via fixture, so used tags must be non-empty
    used_names = [t["name"] for t in body2["tags"]]
    assert "models" in used_names
    assert "checkpoints" in used_names

    # Prefix filter should refine the list
    r3 = http.get(api_base + "/api/tags", params={"include_zero": "false", "prefix": "uni"}, timeout=120)
    b3 = r3.json()
    assert r3.status_code == 200
    names3 = [t["name"] for t in b3["tags"]]
    assert "unit-tests" in names3
    assert "models" not in names3  # filtered out by prefix

    # Order by name ascending should be stable
    r4 = http.get(api_base + "/api/tags", params={"include_zero": "false", "order": "name_asc"}, timeout=120)
    b4 = r4.json()
    assert r4.status_code == 200
    names4 = [t["name"] for t in b4["tags"]]
    assert names4 == sorted(names4)