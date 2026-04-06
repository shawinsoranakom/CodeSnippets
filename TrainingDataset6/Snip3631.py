def test_required_list_str_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": True,
                "schema": {
                    "title": "P",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "name": "p",
                "in": "query",
            }
        ]
    )