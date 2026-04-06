def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/next": {
                    "get": {
                        "summary": "Read Next Item",
                        "operationId": "read_next_item_items_next_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {"$ref": "#/components/schemas/Item"}
                                    }
                                },
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "Item": {
                        "title": "Item",
                        "required": ["name", "price"],
                        "type": "object",
                        "properties": {
                            "name": {"title": "Name", "type": "string"},
                            "price": {"title": "Price", "type": "number"},
                            "tags": {
                                "title": "Tags",
                                "type": "array",
                                "items": {"type": "string"},
                            },
                            "description": {
                                "title": "Description",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "tax": {
                                "title": "Tax",
                                "anyOf": [{"type": "number"}, {"type": "null"}],
                            },
                        },
                    }
                }
            },
        }
    )