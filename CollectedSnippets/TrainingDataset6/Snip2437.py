def test_override_with_sub_router_depends():
    app.dependency_overrides[common_parameters] = overrider_dependency_with_sub
    response = client.get("/router-depends/")
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": ["query", "k"],
                "msg": "Field required",
                "input": None,
            }
        ]
    }

    app.dependency_overrides = {}