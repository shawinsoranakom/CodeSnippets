def test_required_list_alias_and_validation_alias_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": True,
                "schema": {
                    "title": "P Val Alias",
                    "type": "array",
                    "items": {"type": "string"},
                },
                "name": "p_val_alias",
                "in": "header",
            }
        ]
    )