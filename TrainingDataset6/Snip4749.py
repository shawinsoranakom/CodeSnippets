def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/": {
                    "get": {
                        "summary": "Get Items",
                        "operationId": "get_items_items__get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "title": "Response Get Items Items  Get",
                                            "type": "array",
                                            "items": {
                                                "$ref": "#/components/schemas/Item"
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    },
                    "post": {
                        "summary": "Create Item",
                        "operationId": "create_item_items__post",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {"$ref": "#/components/schemas/Item"}
                                }
                            },
                            "required": True,
                        },
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/ResponseMessage"
                                        }
                                    }
                                },
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
                    },
                },
            },
            "components": {
                "schemas": {
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
                    "Item": {
                        "title": "Item",
                        "required": ["name", "price"],
                        "type": "object",
                        "properties": {
                            "name": {"title": "Name", "type": "string"},
                            "price": {"title": "Price", "type": "number"},
                        },
                    },
                    "ResponseMessage": {
                        "title": "ResponseMessage",
                        "required": ["message"],
                        "type": "object",
                        "properties": {
                            "message": {"title": "Message", "type": "string"}
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
                }
            },
        }
    )