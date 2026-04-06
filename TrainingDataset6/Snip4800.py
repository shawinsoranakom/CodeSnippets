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
                                "name": "host",
                                "in": "header",
                                "required": True,
                                "schema": {"type": "string", "title": "Host"},
                            },
                            {
                                "name": "save_data",
                                "in": "header",
                                "required": True,
                                "schema": {"type": "boolean", "title": "Save Data"},
                            },
                            {
                                "name": "if_modified_since",
                                "in": "header",
                                "required": False,
                                "schema": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "title": "If Modified Since",
                                },
                            },
                            {
                                "name": "traceparent",
                                "in": "header",
                                "required": False,
                                "schema": {
                                    "anyOf": [{"type": "string"}, {"type": "null"}],
                                    "title": "Traceparent",
                                },
                            },
                            {
                                "name": "x_tag",
                                "in": "header",
                                "required": False,
                                "schema": {
                                    "type": "array",
                                    "items": {"type": "string"},
                                    "default": [],
                                    "title": "X Tag",
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