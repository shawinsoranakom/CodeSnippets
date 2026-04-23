def test_hashed_asset_two_asset_infos_both_get_missing(
    http: requests.Session,
    api_base: str,
    comfy_tmp_base_dir: Path,
    asset_factory,
):
    """Hashed asset with a single cache_state, but two AssetInfo rows:
       deleting the single file then syncing should add 'missing' to both infos.
    """
    # Upload one hashed asset
    name = "two_infos_one_path.png"
    base_tags = ["input", "unit-tests", "multiinfo"]
    created = asset_factory(name, base_tags, {}, b"A" * 2048)

    # Create second AssetInfo for the same Asset via from-hash
    payload = {
        "hash": created["asset_hash"],
        "name": "two_infos_one_path_copy.png",
        "tags": base_tags,  # keep it in our unit-tests scope for cleanup
        "user_metadata": {"k": "v"},
    }
    r2 = http.post(api_base + "/api/assets/from-hash", json=payload, timeout=120)
    b2 = r2.json()
    assert r2.status_code == 201, b2
    second_id = b2["id"]

    # Remove the single underlying file
    p = comfy_tmp_base_dir / "input" / "unit-tests" / "multiinfo" / get_asset_filename(b2["asset_hash"], ".png")
    assert p.exists()
    p.unlink()

    r0 = http.get(api_base + "/api/tags", params={"limit": "1000", "include_zero": "false"}, timeout=120)
    tags0 = r0.json()
    assert r0.status_code == 200, tags0
    byname0 = {t["name"]: t for t in tags0.get("tags", [])}
    old_missing = int(byname0.get("missing", {}).get("count", 0))

    # Sync -> both AssetInfos for this asset must receive 'missing'
    trigger_sync_seed_assets(http, api_base)

    ga = http.get(f"{api_base}/api/assets/{created['id']}", timeout=120)
    da = ga.json()
    assert ga.status_code == 200, da
    assert "missing" in set(da.get("tags", []))

    gb = http.get(f"{api_base}/api/assets/{second_id}", timeout=120)
    db = gb.json()
    assert gb.status_code == 200, db
    assert "missing" in set(db.get("tags", []))

    # Tag usage for 'missing' increased by exactly 2 (two AssetInfos)
    r1 = http.get(api_base + "/api/tags", params={"limit": "1000", "include_zero": "false"}, timeout=120)
    tags1 = r1.json()
    assert r1.status_code == 200, tags1
    byname1 = {t["name"]: t for t in tags1.get("tags", [])}
    new_missing = int(byname1.get("missing", {}).get("count", 0))
    assert new_missing == old_missing + 2