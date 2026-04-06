def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/images/multiple/": {
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
                        "summary": "Create Multiple Images",
                        "operationId": "create_multiple_images_images_multiple__post",
                        "requestBody": {
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "title": "Images",
                                        "type": "array",
                                        "items": {"$ref": "#/components/schemas/Image"},
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