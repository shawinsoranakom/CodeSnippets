def test_header_param_model_invalid(client: TestClient):
    response = client.get("/items/")
    assert response.status_code == 422
    assert response.json() == snapshot(
        {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["header", "save_data"],
                    "msg": "Field required",
                    "input": {
                        "x_tag": [],
                        "host": "testserver",
                        "accept": "*/*",
                        "accept-encoding": "gzip, deflate",
                        "connection": "keep-alive",
                        "user-agent": "testclient",
                    },
                }
            ]
        }
    )