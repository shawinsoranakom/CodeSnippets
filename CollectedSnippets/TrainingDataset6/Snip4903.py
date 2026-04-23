def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/{item_id}": {
                    "get": {
                        "summary": "Read Items",
                        "operationId": "read_items_items__item_id__get",
                        "parameters": [
                            {
                                "required": True,
                                "schema": {
                                    "title": "The ID of the item to get",
                                    "type": "integer",
                                },
                                "name": "item_id",
                                "in": "path",
                            },
                            {
                                "required": True,
                                "schema": {
                                    "type": "string",
                                    "title": "Q",
                                },
                                "name": "q",
                                "in": "query",
                            },
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {},
                                    }
                                },
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
                    "HTTPValidationError": {
                        "properties": {
                            "detail": {
                                "items": {
                                    "$ref": "#/components/schemas/ValidationError",
                                },
                                "title": "Detail",
                                "type": "array",
                            },
                        },
                        "title": "HTTPValidationError",
                        "type": "object",
                    },
                    "ValidationError": {
                        "properties": {
                            "ctx": {"title": "Context", "type": "object"},
                            "input": {"title": "Input"},
                            "loc": {
                                "items": {
                                    "anyOf": [
                                        {
                                            "type": "string",
                                        },
                                        {
                                            "type": "integer",
                                        },
                                    ],
                                },
                                "title": "Location",
                                "type": "array",
                            },
                            "msg": {
                                "title": "Message",
                                "type": "string",
                            },
                            "type": {
                                "title": "Error Type",
                                "type": "string",
                            },
                        },
                        "required": [
                            "loc",
                            "msg",
                            "type",
                        ],
                        "title": "ValidationError",
                        "type": "object",
                    },
                },
            },
        }
    )