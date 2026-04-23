def test_metadata_filename_is_set_for_seed_asset_without_hash(
    root: str,
    http: requests.Session,
    api_base: str,
    comfy_tmp_base_dir: Path,
):
    """Seed ingest (no hash yet) must compute user_metadata['filename'] immediately."""
    scope = f"seedmeta-{uuid.uuid4().hex[:6]}"
    name = "seed_filename.bin"

    base = comfy_tmp_base_dir / root / "unit-tests" / scope / "a" / "b"
    base.mkdir(parents=True, exist_ok=True)
    fp = base / name
    fp.write_bytes(b"Z" * 2048)

    trigger_sync_seed_assets(http, api_base)

    r1 = http.get(
        api_base + "/api/assets",
        params={"include_tags": f"unit-tests,{scope}", "name_contains": name},
        timeout=120,
    )
    body = r1.json()
    assert r1.status_code == 200, body
    matches = [a for a in body.get("assets", []) if a.get("name") == name]
    assert matches, "Seed asset should be visible after sync"
    assert matches[0].get("asset_hash") is None  # still a seed
    aid = matches[0]["id"]

    r2 = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    detail = r2.json()
    assert r2.status_code == 200, detail
    filename = (detail.get("user_metadata") or {}).get("filename")
    expected = str(fp.relative_to(comfy_tmp_base_dir / root)).replace("\\", "/")
    assert filename == expected, f"expected filename={expected}, got {filename!r}"