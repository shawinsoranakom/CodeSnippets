def test_query_pass_extra_list():
    client = TestClient(app)
    resp = client.get(
        "/query",
        params={
            "param": "123",
            "param2": ["456", "789"],  # Pass a list of values as extra parameter
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "param": "123",
        "param2": ["456", "789"],
    }