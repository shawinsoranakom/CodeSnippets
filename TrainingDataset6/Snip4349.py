def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/": {
                    "get": {
                        "summary": "Get People",
                        "operationId": "get_people__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "items": {},
                                            "type": "array",
                                            "title": "Response Get People  Get",
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
        }
    )