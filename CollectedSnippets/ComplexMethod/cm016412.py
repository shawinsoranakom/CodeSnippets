def test_seed_asset_removed_when_file_is_deleted(
    root: str,
    http: requests.Session,
    api_base: str,
    comfy_tmp_base_dir: Path,
):
    """Asset without hash (seed) whose file disappears:
       after triggering sync_seed_assets, Asset + AssetInfo disappear.
    """
    # Create a file directly under input/unit-tests/<case> so tags include "unit-tests"
    case_dir = comfy_tmp_base_dir / root / "unit-tests" / "syncseed"
    case_dir.mkdir(parents=True, exist_ok=True)
    name = f"seed_{uuid.uuid4().hex[:8]}.bin"
    fp = case_dir / name
    fp.write_bytes(b"Z" * 2048)

    # Trigger a seed sync so DB sees this path (seed asset => hash is NULL)
    trigger_sync_seed_assets(http, api_base)

    # Verify it is visible via API and carries no hash (seed)
    r1 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,syncseed", "name_contains": name},
        timeout=120,
    )
    body1 = r1.json()
    assert r1.status_code == 200
    # there should be exactly one with that name
    matches = [a for a in body1.get("assets", []) if a.get("name") == name]
    assert matches
    assert matches[0].get("asset_hash") is None
    asset_info_id = matches[0]["id"]

    # Remove the underlying file and sync again
    if fp.exists():
        fp.unlink()

    trigger_sync_seed_assets(http, api_base)

    # It should disappear (AssetInfo and seed Asset gone)
    r2 = http.get(
        api_base + "/api/assets",
        params={"include_tags": "unit-tests,syncseed", "name_contains": name},
        timeout=120,
    )
    body2 = r2.json()
    assert r2.status_code == 200
    matches2 = [a for a in body2.get("assets", []) if a.get("name") == name]
    assert not matches2, f"Seed asset {asset_info_id} should be gone after sync"