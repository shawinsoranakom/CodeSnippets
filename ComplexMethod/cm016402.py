def test_add_and_remove_tags(http: requests.Session, api_base: str, seeded_asset: dict):
    aid = seeded_asset["id"]

    # Add tags with duplicates and mixed case
    payload_add = {"tags": ["NewTag", "unit-tests", "newtag", "BETA"]}
    r1 = http.post(f"{api_base}/api/assets/{aid}/tags", json=payload_add, timeout=120)
    b1 = r1.json()
    assert r1.status_code == 200, b1
    # normalized, deduplicated; 'unit-tests' was already present from the seed
    assert set(b1["added"]) == {"newtag", "beta"}
    assert set(b1["already_present"]) == {"unit-tests"}
    assert "newtag" in b1["total_tags"] and "beta" in b1["total_tags"]

    rg = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    g = rg.json()
    assert rg.status_code == 200
    tags_now = set(g["tags"])
    assert {"newtag", "beta"}.issubset(tags_now)

    # Remove a tag and a non-existent tag
    payload_del = {"tags": ["newtag", "does-not-exist"]}
    r2 = http.delete(f"{api_base}/api/assets/{aid}/tags", json=payload_del, timeout=120)
    b2 = r2.json()
    assert r2.status_code == 200
    assert set(b2["removed"]) == {"newtag"}
    assert set(b2["not_present"]) == {"does-not-exist"}

    # Verify remaining tags after deletion
    rg2 = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    g2 = rg2.json()
    assert rg2.status_code == 200
    tags_later = set(g2["tags"])
    assert "newtag" not in tags_later
    assert "beta" in tags_later