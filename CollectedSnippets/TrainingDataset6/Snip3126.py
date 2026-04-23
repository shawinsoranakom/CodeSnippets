def test_header_pass_extra_list():
    client = TestClient(app)

    resp = client.get(
        "/header",
        headers=[
            ("param", "123"),
            ("param2", "456"),  # Pass a list of values as extra parameter
            ("param2", "789"),
        ],
    )
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "param2" in resp_json
    assert resp_json["param2"] == ["456", "789"]