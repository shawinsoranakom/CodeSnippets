def test_required_alias_by_name(path: str):
    client = TestClient(app)
    client.cookies.set("p", "hello")
    response = client.get(path)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["cookie", "p_alias"],
                "msg": "Field required",
                "input": IsOneOf(
                    None,
                    {"p": "hello"},
                ),
            }
        ]
    }