def test_header_param_model_extra(client: TestClient):
    response = client.get(
        "/items/", headers=[("save-data", "true"), ("tool", "plumbus")]
    )
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "host": "testserver",
            "save_data": True,
            "if_modified_since": None,
            "traceparent": None,
            "x_tag": [],
        }
    )