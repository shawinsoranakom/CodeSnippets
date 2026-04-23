def test_required_str_alias_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": True,
                "schema": {"title": "P Alias", "type": "string"},
                "name": "p_alias",
                "in": "header",
            }
        ]
    )