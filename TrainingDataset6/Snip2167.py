def test_openapi_schema(client: TestClient):
    response = client.get("openapi.json")
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/": {
                    "get": {
                        "summary": "Test",
                        "operationId": "test__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/MyModel"
                                        }
                                    }
                                },
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "MyModel": {
                        "properties": {
                            "custom_field": {
                                "items": {"type": "number"},
                                "type": "array",
                                "title": "Custom Field",
                            }
                        },
                        "type": "object",
                        "required": ["custom_field"],
                        "title": "MyModel",
                    }
                }
            },
        }
    )