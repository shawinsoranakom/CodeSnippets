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
                        "summary": "Read Items",
                        "operationId": "read_items_items__get",
                        "parameters": [
                            {
                                "name": "limit",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "maximum": 100,
                                    "exclusiveMinimum": 0,
                                    "default": 100,
                                    "title": "Limit",
                                },
                            },
                            {
                                "name": "offset",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "integer",
                                    "minimum": 0,
                                    "default": 0,
                                    "title": "Offset",
                                },
                            },
                            {
                                "name": "order_by",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "enum": ["created_at", "updated_at"],
                                    "type": "string",
                                    "default": "created_at",
                                    "title": "Order By",
                                },
                            },
                            {
                                "name": "tags",
                                "in": "query",
                                "required": False,
                                "schema": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "default": [],
                                    "title": "Tags",
                                },
                            },
                        ],
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
                    }
                }
            },
            "components": {
                "schemas": {
                    "HTTPValidationError": {
                        "properties": {
                            "detail": {
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError"
                                },
                                "type": "array",
                                "title": "Detail",
                            }
                        },
                        "type": "object",
                        "title": "HTTPValidationError",
                    },
                    "ValidationError": {
                        "properties": {
                            "ctx": {"title": "Context", "type": "object"},
                            "input": {"title": "Input"},
                            "loc": {
                                "items": {
                                    "anyOf": [{"type": "string"}, {"type": "integer"}]
                                },
                                "type": "array",
                                "title": "Location",
                            },
                            "msg": {"type": "string", "title": "Message"},
                            "type": {"type": "string", "title": "Error Type"},
                        },
                        "type": "object",
                        "required": ["loc", "msg", "type"],
                        "title": "ValidationError",
                    },
                }
            },
        }
    )