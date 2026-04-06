def test_header_param_model_defaults(client: TestClient):
    response = client.get("/items/", headers=[("save_data", "true")])
    assert response.status_code == 200
    assert response.json() == {
        "host": "testserver",
        "save_data": True,
        "if_modified_since": None,
        "traceparent": None,
        "x_tag": [],
    }