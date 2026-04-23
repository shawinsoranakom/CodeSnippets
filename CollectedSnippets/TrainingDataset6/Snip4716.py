def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/{id}": {
                    "put": {
                        "operationId": "update_item_items__id__put",
                        "parameters": [
                            {
                                "in": "path",
                                "name": "id",
                                "required": True,
                                "schema": {
                                    "title": "Id",
                                    "type": "string",
                                },
                            },
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Item",
                                    },
                                },
                            },
                            "required": True,
                        },
                        "responses": {
                            "200": {
                                "content": {
                                    "application/json": {
                                        "schema": {},
                                    },
                                },
                                "description": "Successful Response",
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
                        "summary": "Update Item",
                    },
                },
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
                    "Item": {
                        "properties": {
                            "description": {
                                "anyOf": [
                                    {
                                        "type": "string",
                                    },
                                    {
                                        "type": "null",
                                    },
                                ],
                                "title": "Description",
                            },
                            "timestamp": {
                                "format": "date-time",
                                "title": "Timestamp",
                                "type": "string",
                            },
                            "title": {
                                "title": "Title",
                                "type": "string",
                            },
                        },
                        "required": [
                            "title",
                            "timestamp",
                        ],
                        "title": "Item",
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