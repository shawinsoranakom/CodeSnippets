def test_openapi_schema(client: TestClient):
    response = client.get("/openapi.json")
    assert response.status_code == 200, response.text
    assert response.json() == snapshot(
        {
            "openapi": "3.1.0",
            "info": {"title": "FastAPI", "version": "0.1.0"},
            "paths": {
                "/story/stream": {
                    "get": {
                        "summary": "Stream Story",
                        "operationId": "stream_story_story_stream_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-no-async": {
                    "get": {
                        "summary": "Stream Story No Async",
                        "operationId": "stream_story_no_async_story_stream_no_async_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-no-annotation": {
                    "get": {
                        "summary": "Stream Story No Annotation",
                        "operationId": "stream_story_no_annotation_story_stream_no_annotation_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-no-async-no-annotation": {
                    "get": {
                        "summary": "Stream Story No Async No Annotation",
                        "operationId": "stream_story_no_async_no_annotation_story_stream_no_async_no_annotation_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-bytes": {
                    "get": {
                        "summary": "Stream Story Bytes",
                        "operationId": "stream_story_bytes_story_stream_bytes_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-no-async-bytes": {
                    "get": {
                        "summary": "Stream Story No Async Bytes",
                        "operationId": "stream_story_no_async_bytes_story_stream_no_async_bytes_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-no-annotation-bytes": {
                    "get": {
                        "summary": "Stream Story No Annotation Bytes",
                        "operationId": "stream_story_no_annotation_bytes_story_stream_no_annotation_bytes_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
                "/story/stream-no-async-no-annotation-bytes": {
                    "get": {
                        "summary": "Stream Story No Async No Annotation Bytes",
                        "operationId": "stream_story_no_async_no_annotation_bytes_story_stream_no_async_no_annotation_bytes_get",
                        "responses": {
                            "200": {
                                "description": "Successful Response",
                            }
                        },
                    }
                },
            },
        }
    )