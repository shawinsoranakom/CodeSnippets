def test_header_param_model_no_underscore(client: TestClient):
    response = client.get(
        "/items/",
        headers=[
            ("save-data", "true"),
            ("if-modified-since", "yesterday"),
            ("traceparent", "123"),
            ("x-tag", "one"),
            ("x-tag", "two"),
        ],
    )
    assert response.status_code == 422
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["header", "save_data"],
                    "msg": "Field required",
                    "input": {
                        "host": "testserver",
                        "traceparent": "123",
                        "x_tag": [],
                        "accept": "*/*",
                        "accept-encoding": "gzip, deflate",
                        "connection": "keep-alive",
                        "user-agent": "testclient",
                        "save-data": "true",
                        "if-modified-since": "yesterday",
                        "x-tag": ["one", "two"],
                    },
                }
            ]
        }
    )