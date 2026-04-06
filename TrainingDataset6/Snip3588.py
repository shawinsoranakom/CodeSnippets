def test_optional_validation_alias_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": False,
                "schema": {
                    "anyOf": [{"type": "string"}, {"type": "null"}],
                    "title": "P Val Alias",
                },
                "name": "p_val_alias",
                "in": "header",
            }
        ]
    )