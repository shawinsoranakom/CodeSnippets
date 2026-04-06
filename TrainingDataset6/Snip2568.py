def test_router_level_dep_scope_function() -> None:
    response = client.get("/router-scope-function/")
    assert response.status_code == 503
    assert response.json() == {"detail": "Exception after yield"}