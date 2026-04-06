def test_router_depends():
    response = client.get("/router-depends/")
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