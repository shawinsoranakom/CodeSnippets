def test_get_and_delete_asset(http: requests.Session, api_base: str, seeded_asset: dict):
    aid = seeded_asset["id"]

    # GET detail
    rg = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    detail = rg.json()
    assert rg.status_code == 200, detail
    assert detail["id"] == aid
    assert "user_metadata" in detail
    assert "filename" in detail["user_metadata"]

    # DELETE (hard delete to also remove underlying asset and file)
    rd = http.delete(f"{api_base}/api/assets/{aid}?delete_content=true", timeout=120)
    assert rd.status_code == 204

    # GET again -> 404
    rg2 = http.get(f"{api_base}/api/assets/{aid}", timeout=120)
    body = rg2.json()
    assert rg2.status_code == 404
    assert body["error"]["code"] == "ASSET_NOT_FOUND"