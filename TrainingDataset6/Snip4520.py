def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "info": {
                "title": "FastAPI",
                "version": "0.1.0",
            },
            "openapi": "3.1.0",
            "paths": {
                "/items/{item_id}": {
                    "put": {
                        "operationId": "update_item_items__item_id__put",
                        "parameters": [
                            {
                                "in": "path",
                                "name": "item_id",
                                "required": True,
                                "schema": {
                                    "title": "Item Id",
                                    "type": "integer",
                                },
                            },
                        ],
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Body_update_item_items__item_id__put",
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
                    "Body_update_item_items__item_id__put": {
                        "properties": {
                            "item": {
                                "$ref": "#/components/schemas/Item",
                            },
                        },
                        "required": ["item"],
                        "title": "Body_update_item_items__item_id__put",
                        "type": "object",
                    },
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
                            "name": {
                                "title": "Name",
                                "type": "string",
                            },
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