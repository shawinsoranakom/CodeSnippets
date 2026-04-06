def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/offers/": {
                    "post": {
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
                        "summary": "Create Offer",
                        "operationId": "create_offer_offers__post",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "$ref": "#/components/schemas/Offer",
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
                    "Image": {
                        "properties": {
                            "url": {
                                "title": "Url",
                                "type": "string",
                                "format": "uri",
                                "maxLength": 2083,
                                "minLength": 1,
                            },
                            "name": {
                                "title": "Name",
                                "type": "string",
                            },
                        },
                        "required": ["url", "name"],
                        "title": "Image",
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
                            "price": {
                                "title": "Price",
                                "type": "number",
                            },
                            "tax": {
                                "title": "Tax",
                                "anyOf": [{"type": "number"}, {"type": "null"}],
                            },
                            "tags": {
                                "title": "Tags",
                                "default": [],
                                "type": "array",
                                "items": {"type": "string"},
                                "uniqueItems": True,
                            },
                            "images": {
                                "anyOf": [
                                    {
                                        "items": {
                                            "$ref": "#/components/schemas/Image",
                                        },
                                        "type": "array",
                                    },
                                    {
                                        "type": "null",
                                    },
                                ],
                                "title": "Images",
                            },
                        },
                        "required": [
                            "name",
                            "price",
                        ],
                        "title": "Item",
                        "type": "object",
                    },
                    "Offer": {
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
                            "items": {
                                "title": "Items",
                                "type": "array",
                                "items": {"$ref": "#/components/schemas/Item"},
                            },
                        },
                        "required": ["name", "price", "items"],
                        "title": "Offer",
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