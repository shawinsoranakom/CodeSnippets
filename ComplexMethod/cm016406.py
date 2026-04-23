def test_concurrent_upload_identical_bytes_different_names(
    root: str,
    http: requests.Session,
    api_base: str,
    make_asset_bytes,
):
    """
    Two concurrent uploads of identical bytes but different names.
    Expect a single Asset (same hash), two AssetReference rows, and exactly one created_new=True.
    """
    scope = f"concupload-{uuid.uuid4().hex[:6]}"
    name1, name2 = "cu_a.bin", "cu_b.bin"
    data = make_asset_bytes("concurrent", 4096)
    tags = [root, "unit-tests", scope]

    def _do_upload(args):
        url, form_data, files_data = args
        with requests.Session() as s:
            return s.post(url, data=form_data, files=files_data, timeout=120)

    url = api_base + "/api/assets"
    form1 = {"tags": json.dumps(tags), "name": name1, "user_metadata": json.dumps({})}
    files1 = {"file": (name1, data, "application/octet-stream")}
    form2 = {"tags": json.dumps(tags), "name": name2, "user_metadata": json.dumps({})}
    files2 = {"file": (name2, data, "application/octet-stream")}

    with ThreadPoolExecutor(max_workers=2) as executor:
        futures = list(executor.map(_do_upload, [(url, form1, files1), (url, form2, files2)]))
    r1, r2 = futures

    b1, b2 = r1.json(), r2.json()
    assert r1.status_code in (200, 201), b1
    assert r2.status_code in (200, 201), b2
    assert b1["asset_hash"] == b2["asset_hash"]
    assert b1["id"] != b2["id"]

    created_flags = sorted([bool(b1.get("created_new")), bool(b2.get("created_new"))])
    assert created_flags == [False, True]

    rl = http.get(
        api_base + "/api/assets",
        params={"include_tags": f"unit-tests,{scope}", "sort": "name"},
        timeout=120,
    )
    bl = rl.json()
    assert rl.status_code == 200, bl
    names = [a["name"] for a in bl.get("assets", [])]
    assert set([name1, name2]).issubset(names)