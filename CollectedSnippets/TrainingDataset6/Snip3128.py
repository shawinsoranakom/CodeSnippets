def test_cookie_pass_extra_list():
    client = TestClient(app)
    client.cookies = [
        ("param", "123"),
        ("param2", "456"),  # Pass a list of values as extra parameter
        ("param2", "789"),
    ]
    resp = client.get("/cookie")
    assert resp.status_code == 200
    resp_json = resp.json()
    assert "param2" in resp_json
    assert resp_json["param2"] == "789"