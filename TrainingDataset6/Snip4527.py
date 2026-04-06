def test_openapi_schema(client: TestClient, mod_name: str):
    tags_schema = {"default": [], "title": "Tags"}
    if mod_name.startswith("tutorial001"):
        tags_schema.update(UNTYPED_LIST_SCHEMA)
    elif mod_name.startswith("tutorial002"):
        tags_schema.update(LIST_OF_STR_SCHEMA)
    elif mod_name.startswith("tutorial003"):
        tags_schema.update(SET_OF_STR_SCHEMA)

    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/{item_id}": {
                    "put": {
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
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Item",
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
                        "properties": {
                            "name": {
                                "title": "Name",
                                "type": "string",
                            },
                            "description": {
                                "title": "Description",
                                "anyOf": [{"type": "string"}, {"type": "null"}],
                            },
                            "price": {
                                "title": "Price",
                                "type": "number",
                            },
                            "tax": {
                                "title": "Tax",
                                "anyOf": [{"type": "number"}, {"type": "null"}],
                            },
                            "tags": Is(tags_schema),
                        },
                        "required": [
                            "name",
                            "price",
                        ],
                        "title": "Item",
                        "type": "object",
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