def test_fastpass_removes_stale_state_row_no_missing(
    root: str,
    http: requests.Session,
    api_base: str,
    comfy_tmp_base_dir: Path,
    asset_factory,
    make_asset_bytes,
    run_scan_and_wait,
):
    """
    Hashed asset with two states:
      - delete one file
      - run fast pass only
    Expect:
      - asset stays healthy (no 'missing')
      - stale AssetCacheState row for the deleted path is removed.
        We verify this behaviorally by recreating the deleted path and running fast pass again:
        a new *seed* AssetInfo is created, which proves the old state row was not reused.
    """
    scope = f"stale-{uuid.uuid4().hex[:6]}"
    name = "two_states.bin"
    data = make_asset_bytes(name, 2048)

    # Upload hashed asset at path1
    a = asset_factory(name, [root, "unit-tests", scope], {}, data)
    base = comfy_tmp_base_dir / root / "unit-tests" / scope
    a1_filename = get_asset_filename(a["asset_hash"], ".bin")
    p1 = base / a1_filename
    assert p1.exists()

    aid = a["id"]
    h = a["asset_hash"]

    # Create second state path2, seed+scan to dedupe into the same Asset
    p2 = base / "copy" / name
    p2.parent.mkdir(parents=True, exist_ok=True)
    p2.write_bytes(data)
    trigger_sync_seed_assets(http, api_base)
    run_scan_and_wait(root)

    # Delete path1 and run fast pass -> no 'missing' and stale state row should be removed
    p1.unlink()
    trigger_sync_seed_assets(http, api_base)
    g1 = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    d1 = g1.json()
    assert g1.status_code == 200, d1
    assert "missing" not in set(d1.get("tags", []))

    # Recreate path1 and run fast pass again.
    # If the stale state row was removed, a NEW seed AssetInfo will appear for this path.
    p1.write_bytes(data)
    trigger_sync_seed_assets(http, api_base)

    rl = http.get(
        api_base + "/api/assets",
        params={"include_tags": f"unit-tests,{scope}"},
        timeout=120,
    )
    bl = rl.json()
    assert rl.status_code == 200, bl
    items = bl.get("assets", [])
    # one hashed AssetInfo (asset_hash == h) + one seed AssetInfo (asset_hash == null)
    hashes = [it.get("asset_hash") for it in items if it.get("name") in (name, a1_filename)]
    assert h in hashes
    assert any(x is None for x in hashes), "Expected a new seed AssetInfo for the recreated path"

    # Asset identity still healthy
    rh = http.head(f"{api_base}/api/assets/hash/{h}", timeout=120)
    assert rh.status_code == 200