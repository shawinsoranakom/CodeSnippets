def test_openapi_schema():
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "Minimal FastAPI App", "version": "1.0.0"},
            "paths": {
                "/messages": {
                    "post": {
                        "summary": "Create Message",
                        "operationId": "create_message_messages_post",
                        "parameters": [
                            {
                                "name": "input_message",
                                "in": "query",
                                "required": True,
                                "schema": {"type": "string", "title": "Input Message"},
                            }
                        ],
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                                "content": {
                                    "application/json": {
                                        "schema": {
                                            "$ref": "#/components/schemas/Message"
                                        }
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
                    "Message": {
                        "properties": {
                            "input": {"type": "string", "title": "Input"},
                            "output": {"$ref": "#/components/schemas/MessageOutput"},
                        },
                        "type": "object",
                        "required": ["input", "output"],
                        "title": "Message",
                    },
                    "MessageEvent": {
                        "properties": {
                            "event_type": {
                                "$ref": "#/components/schemas/MessageEventType",
                                "default": "alpha",
                            },
                            "output": {"type": "string", "title": "Output"},
                        },
                        "type": "object",
                        "required": ["output"],
                        "title": "MessageEvent",
                    },
                    "MessageEventType": {
                        "type": "string",
                        "enum": ["alpha", "beta"],
                        "title": "MessageEventType",
                    },
                    "MessageOutput": {
                        "properties": {
                            "body": {"type": "string", "title": "Body", "default": ""},
                            "events": {
                                "items": {"$ref": "#/components/schemas/MessageEvent"},
                                "type": "array",
                                "title": "Events",
                                "default": [],
                            },
                        },
                        "type": "object",
                        "title": "MessageOutput",
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