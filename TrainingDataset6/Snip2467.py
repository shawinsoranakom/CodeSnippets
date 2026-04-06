def test_dependency_types_with_partial(route: str, value: str) -> None:
    response = client.get(route)
    assert response.status_code == 200, response.text
    assert response.json() == value