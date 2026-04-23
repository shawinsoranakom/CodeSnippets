def test_hashed_asset_two_cache_states_partial_delete_then_full_delete(
    http: requests.Session,
    api_base: str,
    comfy_tmp_base_dir: Path,
    asset_factory,
    make_asset_bytes,
    run_scan_and_wait,
):
    """Hashed asset with two cache_state rows:
       1. delete one file -> sync should NOT add 'missing'
       2. delete second file -> sync should add 'missing'
    """
    name = "two_cache_states_partial_delete.png"
    tags = ["input", "unit-tests", "dual"]
    data = make_asset_bytes(name, 3072)

    created = asset_factory(name, tags, {}, data)
    path1 = comfy_tmp_base_dir / "input" / "unit-tests" / "dual" / get_asset_filename(created["asset_hash"], ".png")
    assert path1.exists()

    # Create a second on-disk copy under the same root but different subfolder
    path2 = comfy_tmp_base_dir / "input" / "unit-tests" / "dual_copy" / name
    path2.parent.mkdir(parents=True, exist_ok=True)
    path2.write_bytes(data)

    # Fast seed so the second path appears (as a seed initially)
    trigger_sync_seed_assets(http, api_base)

    # Deduplication of AssetInfo-s will not happen as first AssetInfo has owner='default' and second has empty owner.
    run_scan_and_wait("input")

    # Remove only one file and sync -> asset should still be healthy (no 'missing')
    path1.unlink()
    trigger_sync_seed_assets(http, api_base)

    g1 = http.get(f"{api_base}/api/assets/{created['id']}", timeout=120)
    d1 = g1.json()
    assert g1.status_code == 200, d1
    assert "missing" not in set(d1.get("tags", [])), "Should not be missing while one valid path remains"

    # Baseline 'missing' usage count just before last file removal
    r0 = http.get(api_base + "/api/tags", params={"limit": "1000", "include_zero": "false"}, timeout=120)
    tags0 = r0.json()
    assert r0.status_code == 200, tags0
    old_missing = int({t["name"]: t for t in tags0.get("tags", [])}.get("missing", {}).get("count", 0))

    # Remove the second (last) file and sync -> now we expect 'missing' on this AssetInfo
    path2.unlink()
    trigger_sync_seed_assets(http, api_base)

    g2 = http.get(f"{api_base}/api/assets/{created['id']}", timeout=120)
    d2 = g2.json()
    assert g2.status_code == 200, d2
    assert "missing" in set(d2.get("tags", [])), "Missing must be set once no valid paths remain"

    # Tag usage for 'missing' increased by exactly 2 (two AssetInfo for one Asset)
    r1 = http.get(api_base + "/api/tags", params={"limit": "1000", "include_zero": "false"}, timeout=120)
    tags1 = r1.json()
    assert r1.status_code == 200, tags1
    new_missing = int({t["name"]: t for t in tags1.get("tags", [])}.get("missing", {}).get("count", 0))
    assert new_missing == old_missing + 2