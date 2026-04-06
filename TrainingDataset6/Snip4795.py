def test_header_param_model(client: TestClient):
    response = client.get(
        "/items/",
        headers=[
            ("save_data", "true"),
            ("if_modified_since", "yesterday"),
            ("traceparent", "123"),
            ("x_tag", "one"),
            ("x_tag", "two"),
        ],
    )
    assert response.status_code == 200
    assert response.json() == {
        "host": "testserver",
        "save_data": True,
        "if_modified_since": "yesterday",
        "traceparent": "123",
        "x_tag": ["one", "two"],
    }