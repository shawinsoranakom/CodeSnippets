def test_required_alias_and_validation_alias_missing(
    path: str, json: dict[str, Any] | None
):
    client = TestClient(app)
    response = client.post(path, json=json)
    assert response.status_code == 422
    assert response.json() == {
        "detail": [
            {
                "type": "missing",
                "loc": IsOneOf(["body"], ["body", "p_val_alias"]),
                "msg": "Field required",
                "input": IsOneOf(None, {}),
            }
        ]
    }