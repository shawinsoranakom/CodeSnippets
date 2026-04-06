def test_list_alias_by_name(path: str):
    client = TestClient(app)
    response = client.post(path, files=[("p", b"hello"), ("p", b"world")])
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["body", "p_alias"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }