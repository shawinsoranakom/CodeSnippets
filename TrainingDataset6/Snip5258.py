def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/items/stream": {
                    "get": {
                        "summary": "Sse Items",
                        "operationId": "sse_items_items_stream_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "text/event-stream": {
                                        "itemSchema": {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "type": "string",
                                                    "contentMediaType": "application/json",
                                                    "contentSchema": {
                                                        "$ref": "#/components/schemas/Item"
                                                    },
                                                },
                                                "event": {"type": "string"},
                                                "id": {"type": "string"},
                                                "retry": {
                                                    "type": "integer",
                                                    "minimum": 0,
                                                },
                                            },
                                            "required": ["data"],
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/items/stream-no-async": {
                    "get": {
                        "summary": "Sse Items No Async",
                        "operationId": "sse_items_no_async_items_stream_no_async_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "text/event-stream": {
                                        "itemSchema": {
                                            "type": "object",
                                            "properties": {
                                                "data": {
                                                    "type": "string",
                                                    "contentMediaType": "application/json",
                                                    "contentSchema": {
                                                        "$ref": "#/components/schemas/Item"
                                                    },
                                                },
                                                "event": {"type": "string"},
                                                "id": {"type": "string"},
                                                "retry": {
                                                    "type": "integer",
                                                    "minimum": 0,
                                                },
                                            },
                                            "required": ["data"],
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/items/stream-no-annotation": {
                    "get": {
                        "summary": "Sse Items No Annotation",
                        "operationId": "sse_items_no_annotation_items_stream_no_annotation_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "text/event-stream": {
                                        "itemSchema": {
                                            "type": "object",
                                            "properties": {
                                                "data": {"type": "string"},
                                                "event": {"type": "string"},
                                                "id": {"type": "string"},
                                                "retry": {
                                                    "type": "integer",
                                                    "minimum": 0,
                                                },
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
                "/items/stream-no-async-no-annotation": {
                    "get": {
                        "summary": "Sse Items No Async No Annotation",
                        "operationId": "sse_items_no_async_no_annotation_items_stream_no_async_no_annotation_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "text/event-stream": {
                                        "itemSchema": {
                                            "type": "object",
                                            "properties": {
                                                "data": {"type": "string"},
                                                "event": {"type": "string"},
                                                "id": {"type": "string"},
                                                "retry": {
                                                    "type": "integer",
                                                    "minimum": 0,
                                                },
                                            },
                                        }
                                    }
                                },
                            }
                        },
                    }
                },
            },
            "components": {
                "schemas": {
                    "Item": {
                        "properties": {
                            "name": {"type": "string", "title": "Name"},
                            "description": {
                                "anyOf": [
                                    {"type": "string"},
                                    {"type": "null"},
                                ],
                                "title": "Description",
                            },
                        },
                        "type": "object",
                        "required": ["name", "description"],
                        "title": "Item",
                    }
                }
            },
        }
    )