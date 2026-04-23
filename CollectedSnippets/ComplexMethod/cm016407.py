def test_duplicate_upload_same_display_name_does_not_clobber(
    root: str,
    http: requests.Session,
    api_base: str,
    asset_factory,
    make_asset_bytes,
):
    """
    Two uploads use the same tags and the same display name but different bytes.
    With hash-based filenames, they must NOT overwrite each other. Both assets
    remain accessible and serve their original content.
    """
    scope = f"dup-path-{uuid.uuid4().hex[:6]}"
    display_name = "same_display.bin"

    d1 = make_asset_bytes(scope + "-v1", 1536)
    d2 = make_asset_bytes(scope + "-v2", 2048)
    tags = [root, "unit-tests", scope]

    first = asset_factory(display_name, tags, {}, d1)
    second = asset_factory(display_name, tags, {}, d2)

    assert first["id"] != second["id"]
    assert first["asset_hash"] != second["asset_hash"]  # different content
    assert first["name"] == second["name"] == display_name

    # Both must be independently retrievable
    r1 = http.get(f"{api_base}/api/assets/{first['id']}/content", timeout=120)
    b1 = r1.content
    assert r1.status_code == 200
    assert b1 == d1
    r2 = http.get(f"{api_base}/api/assets/{second['id']}/content", timeout=120)
    b2 = r2.content
    assert r2.status_code == 200
    assert b2 == d2