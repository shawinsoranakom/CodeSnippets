def test_required_alias_by_name(path: str):
    client = TestClient(app)
    response = client.get(path, headers={"p": "hello"})
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["header", "p_alias"],
                "msg": "Field required",
                "input": IsOneOf(None, IsPartialDict({"p": "hello"})),
            }
        ]
    }