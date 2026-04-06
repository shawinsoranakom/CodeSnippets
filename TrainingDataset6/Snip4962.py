def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/users/{user_id}/items/{item_id}": {
                    "get": {
                        "summary": "Read User Item",
                        "operationId": "read_user_item_users__user_id__items__item_id__get",
                        "parameters": [
                            {
                                "required": True,
                                "schema": {"title": "User Id", "type": "integer"},
                                "name": "user_id",
                                "in": "path",
                            },
                            {
                                "required": True,
                                "schema": {"title": "Item Id", "type": "string"},
                                "name": "item_id",
                                "in": "path",
                            },
                            {
                                "required": False,
                                "schema": {
                                    "title": "Q",
                                    "anyOf": [
                                        {
                                            "type": "string",
                                        },
                                        {
                                            "type": "null",
                                        },
                                    ],
                                },
                                "name": "q",
                                "in": "query",
                            },
                            {
                                "required": False,
                                "schema": {
                                    "title": "Short",
                                    "type": "boolean",
                                    "default": False,
                                },
                                "name": "short",
                                "in": "query",
                            },
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {"application/json": {"schema": {}}},
                            },
                            "422": {
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/HTTPValidationError",
                                        },
                                    },
                                },
                                "description": "Validation Error",
                            },
                        },
                    }
                }
            },
            "components": {
                "schemas": {
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