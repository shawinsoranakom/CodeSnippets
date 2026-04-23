def test_optional_list_str_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": False,
                "schema": {
                    "anyOf": [
                        {"items": {"type": "string"}, "type": "array"},
                        {"type": "null"},
                    ],
                    "title": "P",
                },
                "name": "p",
                "in": "header",
            }
        ]
    )