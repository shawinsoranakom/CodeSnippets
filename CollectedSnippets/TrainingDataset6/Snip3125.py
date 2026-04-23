def test_query_pass_extra_single():
    client = TestClient(app)
    resp = client.get(
        "/query",
        params={
            "param": "123",
            "param2": "456",
        },
    )
    assert resp.status_code == 200
    assert resp.json() == {
        "param": "123",
        "param2": "456",
    }