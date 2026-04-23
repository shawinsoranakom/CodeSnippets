def test_header_pass_extra_single():
    client = TestClient(app)

    resp = client.get(
        "/header",
        headers=[
            ("param", "123"),
            ("param2", "456"),
        ],
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "param2" in resp_json
    assert resp_json["param2"] == "456"