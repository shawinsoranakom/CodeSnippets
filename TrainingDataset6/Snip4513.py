def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/{item_id}": {
                    "put": {
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            },
                            "422": {
                                "description": "Validation Error",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HTTPValidationError"
                                        }
                                    }
                                },
                            },
                        },
                        "summary": "Update Item",
                        "operationId": "update_item_items__item_id__put",
                        "parameters": [
                            {
                                "required": True,
                                "schema": {"title": "Item Id", "type": "integer"},
                                "name": "item_id",
                                "in": "path",
                            },
                            {
                                "required": False,
                                "schema": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "title": "Q",
                                },
                                "name": "q",
                                "in": "query",
                            },
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Body_update_item_items__item_id__put"
                                    }
                                }
                            },
                            "required": True,
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
                            "description": {
                                "title": "Description",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "price": {"title": "Price", "type": "number"},
                            "tax": {
                                "title": "Tax",
                                "anyOf": [{"type": "number"}, {"type": "null"}],
                            },
                        },
                    },
                    "User": {
                        "title": "User",
                        "required": ["username"],
                        "type": "object",
                        "properties": {
                            "username": {"title": "Username", "type": "string"},
                            "full_name": {
                                "title": "Full Name",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                        },
                    },
                    "Body_update_item_items__item_id__put": {
                        "title": "Body_update_item_items__item_id__put",
                        "required": ["item", "user", "importance"],
                        "type": "object",
                        "properties": {
                            "item": {"$ref": "#/components/schemas/Item"},
                            "user": {"$ref": "#/components/schemas/User"},
                            "importance": {
                                "title": "Importance",
                                "type": "integer",
                                "exclusiveMinimum": 0.0,
                            },
                        },
                    },
                    "ValidationError": {
                        "title": "ValidationError",
                        "required": ["loc", "msg", "type"],
                        "type": "object",
                        "properties": {
                            "loc": {
                                "title": "Location",
                                "type": "array",
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                            },
                            "msg": {"title": "Message", "type": "string"},
                            "type": {"title": "Error Type", "type": "string"},
                            "input": {"title": "Input"},
                            "ctx": {"title": "Context", "type": "object"},
                        },
                    },
                    "HTTPValidationError": {
                        "title": "HTTPValidationError",
                        "type": "object",
                        "properties": {
                            "detail": {
                                "title": "Detail",
                                "type": "array",
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                            }
                        },
                    },
                }
            },
        }
    )