def test_router_decorator_depends():
    response = client.get("/router-decorator-depends/")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "q"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }