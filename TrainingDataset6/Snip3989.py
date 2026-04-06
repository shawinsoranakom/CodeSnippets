def test_openapi_schema(client: TestClient):
    response = client.get("openapi.json")
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/": {
                    "get": {
                        "summary": "Read Root",
                        "operationId": "read_root__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ModelWithRef"
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
                    "ModelWithRef": {
                        "properties": {"$ref": {"type": "string", "title": "$Ref"}},
                        "type": "object",
                        "required": ["$ref"],
                        "title": "ModelWithRef",
                    }
                }
            },
        }
    )