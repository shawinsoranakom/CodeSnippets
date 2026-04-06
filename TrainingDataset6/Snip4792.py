def test_header_param_model_extra(client: TestClient):
    response = client.get(
        "/items/", headers=[("save-data", "true"), ("tool", "plumbus")]
    )
    assert response.status_code == 422, response.text
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "extra_forbidden",
                    "loc": ["header", "tool"],
                    "msg": "Extra inputs are not permitted",
                    "input": "plumbus",
                }
            ]
        }
    )