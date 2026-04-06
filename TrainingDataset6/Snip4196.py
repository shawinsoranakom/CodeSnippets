def test_security_scopes_dont_propagate():
    response = client.get("/scopes")
    assert response.status_code == 200
    assert response.json() == {
        "dep1": ["scope3", "scope1"],
        "dep2": ["scope3", "scope2"],
    }