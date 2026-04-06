def test_required_validation_alias_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": True,
                "schema": {"title": "P Val Alias", "type": "string"},
                "name": "p_val_alias",
                "in": "header",
            }
        ]
    )