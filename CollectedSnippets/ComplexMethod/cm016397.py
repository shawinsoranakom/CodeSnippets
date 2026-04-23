def test_delete_upon_reference_count(
    http: requests.Session, api_base: str, seeded_asset: dict
):
    # Create a second reference to the same asset via from-hash
    src_hash = seeded_asset["asset_hash"]
    payload = {
        "hash": src_hash,
        "name": "unit_ref_copy.safetensors",
        "tags": ["models", "checkpoints", "unit-tests", "del-flow"],
        "user_metadata": {"note": "copy"},
    }
    r2 = http.post(f"{api_base}/api/assets/from-hash", json=payload, timeout=120)
    copy = r2.json()
    assert r2.status_code == 201, copy
    assert copy["asset_hash"] == src_hash
    assert copy["created_new"] is False

    # Soft-delete original reference (default) -> asset identity must remain
    aid1 = seeded_asset["id"]
    rd1 = http.delete(f"{api_base}/api/assets/{aid1}", timeout=120)
    assert rd1.status_code == 204

    rh1 = http.head(f"{api_base}/api/assets/hash/{src_hash}", timeout=120)
    assert rh1.status_code == 200  # identity still present (second ref exists)

    # Soft-delete the last reference -> asset identity preserved (no hard delete)
    aid2 = copy["id"]
    rd2 = http.delete(f"{api_base}/api/assets/{aid2}", timeout=120)
    assert rd2.status_code == 204

    rh2 = http.head(f"{api_base}/api/assets/hash/{src_hash}", timeout=120)
    assert rh2.status_code == 200  # asset identity preserved (soft delete)

    # Re-associate via from-hash, then hard-delete -> orphan content removed
    r3 = http.post(f"{api_base}/api/assets/from-hash", json=payload, timeout=120)
    assert r3.status_code == 201, r3.json()
    aid3 = r3.json()["id"]

    rd3 = http.delete(f"{api_base}/api/assets/{aid3}?delete_content=true", timeout=120)
    assert rd3.status_code == 204

    rh3 = http.head(f"{api_base}/api/assets/hash/{src_hash}", timeout=120)
    assert rh3.status_code == 404