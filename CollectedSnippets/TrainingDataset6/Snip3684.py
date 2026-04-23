def test_optional_str_alias_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": False,
                "schema": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "P Alias",
                },
                "name": "p_alias",
                "in": "query",
            }
        ]
    )