def test_download_chooses_existing_state_and_updates_access_time(
    root: str,
    http: requests.Session,
    api_base: str,
    comfy_tmp_base_dir: Path,
    asset_factory,
    make_asset_bytes,
    run_scan_and_wait,
):
    """
    Hashed asset with two state paths: if the first one disappears,
    GET /content still serves from the remaining path and bumps last_access_time.
    """
    scope = f"dl-first-{uuid.uuid4().hex[:6]}"
    name = "first_existing_state.bin"
    data = make_asset_bytes(name, 3072)

    # Upload -> path1
    a = asset_factory(name, [root, "unit-tests", scope], {}, data)
    aid = a["id"]

    base = comfy_tmp_base_dir / root / "unit-tests" / scope
    path1 = base / get_asset_filename(a["asset_hash"], ".bin")
    assert path1.exists()

    # Seed path2 by copying, then scan to dedupe into a second state
    path2 = base / "alt" / name
    path2.parent.mkdir(parents=True, exist_ok=True)
    path2.write_bytes(data)
    trigger_sync_seed_assets(http, api_base)
    run_scan_and_wait(root)

    # Remove path1 so server must fall back to path2
    path1.unlink()

    # last_access_time before
    rg0 = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    d0 = rg0.json()
    assert rg0.status_code == 200, d0
    ts0 = d0.get("last_access_time")

    time.sleep(0.05)
    r = http.get(f"{api_base}/api/assets/{aid}/content", timeout=120)
    blob = r.content
    assert r.status_code == 200
    assert blob == data  # must serve from the surviving state (same bytes)

    rg1 = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    d1 = rg1.json()
    assert rg1.status_code == 200, d1
    ts1 = d1.get("last_access_time")

    def _parse_iso8601(s: Optional[str]) -> Optional[float]:
        if not s:
            return None
        s = s[:-1] if s.endswith("Z") else s
        return datetime.fromisoformat(s).timestamp()

    t0 = _parse_iso8601(ts0)
    t1 = _parse_iso8601(ts1)
    assert t1 is not None
    if t0 is not None:
        assert t1 > t0