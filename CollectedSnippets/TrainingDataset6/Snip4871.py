def test_openapi_schema(client: TestClient, mod_name: str):
    mod_name = mod_name[:11]

    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/": {
                    "post": {
                        "summary": "Create an item",
                        "description": Is(DESCRIPTIONS[mod_name]),
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
                                        "schema": {"$ref": "#/components/schemas/Item"}
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
                            "name": {
                                "title": "Name",
                                "type": "string",
                            },
                            "price": {
                                "title": "Price",
                                "type": "number",
                            },
                            "tags": {
                                "default": [],
                                "items": {
                                    "type": "string",
                                },
                                "title": "Tags",
                                "type": "array",
                                "uniqueItems": True,
                            },
                            "tax": {
                                "anyOf": [
                                    {
                                        "type": "number",
                                    },
                                    {
                                        "type": "null",
                                    },
                                ],
                                "title": "Tax",
                            },
                        },
                        "required": [
                            "name",
                            "price",
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