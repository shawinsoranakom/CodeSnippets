def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "info": {
                "title": "FastAPI",
                "version": "0.1.0",
            },
            "openapi": "3.1.0",
            "paths": {
                "/legacy/": {
                    "get": {
                        "operationId": "get_legacy_data_legacy__get",
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {},
                                    },
                                },
                                "description": "Successful Response",
                            },
                        },
                        "summary": "Get Legacy Data",
                    },
                },
            },
        }
    )