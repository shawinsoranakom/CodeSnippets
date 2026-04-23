def test_upload_ok_duplicate_reference(http: requests.Session, api_base: str, make_asset_bytes):
    name = "dup_a.safetensors"
    tags = ["models", "checkpoints", "unit-tests", "alpha"]
    meta = {"purpose": "dup"}
    data = make_asset_bytes(name)
    files = {"file": (name, data, "application/octet-stream")}
    form = {"tags": json.dumps(tags), "name": name, "user_metadata": json.dumps(meta)}
    r1 = http.post(api_base + "/api/assets", data=form, files=files, timeout=120)
    a1 = r1.json()
    assert r1.status_code == 201, a1
    assert a1["created_new"] is True

    # Second upload with the same data and name creates a new AssetReference (duplicates allowed)
    # Returns 200 because Asset already exists, but a new AssetReference is created
    files = {"file": (name, data, "application/octet-stream")}
    form = {"tags": json.dumps(tags), "name": name, "user_metadata": json.dumps(meta)}
    r2 = http.post(api_base + "/api/assets", data=form, files=files, timeout=120)
    a2 = r2.json()
    assert r2.status_code in (200, 201), a2
    assert a2["asset_hash"] == a1["asset_hash"]
    assert a2["id"] != a1["id"]  # new reference with same content

    # Third upload with the same data but different name also creates new AssetReference
    files = {"file": (name, data, "application/octet-stream")}
    form = {"tags": json.dumps(tags), "name": name + "_d", "user_metadata": json.dumps(meta)}
    r3 = http.post(api_base + "/api/assets", data=form, files=files, timeout=120)
    a3 = r3.json()
    assert r3.status_code in (200, 201), a3
    assert a3["asset_hash"] == a1["asset_hash"]
    assert a3["id"] != a1["id"]
    assert a3["id"] != a2["id"]