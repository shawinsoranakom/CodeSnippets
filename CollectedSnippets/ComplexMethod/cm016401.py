def test_tags_empty_usage(http: requests.Session, api_base: str, asset_factory, make_asset_bytes):
    # Baseline: system tags exist when include_zero (default) is true
    r1 = http.get(api_base + "/api/tags", params={"limit": "500"}, timeout=120)
    body1 = r1.json()
    assert r1.status_code == 200
    names = [t["name"] for t in body1["tags"]]
    assert "models" in names and "checkpoints" in names

    # Create a short-lived asset under input with a unique custom tag
    scope = f"tags-empty-usage-{uuid.uuid4().hex[:6]}"
    custom_tag = f"temp-{uuid.uuid4().hex[:8]}"
    name = "tag_seed.bin"
    _asset = asset_factory(
        name,
        ["input", "unit-tests", scope, custom_tag],
        {},
        make_asset_bytes(name, 512),
    )

    # While the asset exists, the custom tag must appear when include_zero=false
    r2 = http.get(
        api_base + "/api/tags",
        params={"include_zero": "false", "prefix": custom_tag, "limit": "50"},
        timeout=120,
    )
    body2 = r2.json()
    assert r2.status_code == 200
    used_names = [t["name"] for t in body2["tags"]]
    assert custom_tag in used_names

    # Hard-delete the asset so the tag usage drops to zero
    rd = http.delete(f"{api_base}/api/assets/{_asset['id']}?delete_content=true", timeout=120)
    assert rd.status_code == 204

    # Now the custom tag must not be returned when include_zero=false
    r3 = http.get(
        api_base + "/api/tags",
        params={"include_zero": "false", "prefix": custom_tag, "limit": "50"},
        timeout=120,
    )
    body3 = r3.json()
    assert r3.status_code == 200
    names_after = [t["name"] for t in body3["tags"]]
    assert custom_tag not in names_after
    assert not names_after