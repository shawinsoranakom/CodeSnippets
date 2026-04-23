def test_required_str_schema(path: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": True,
                "schema": {"title": "P", "type": "string"},
                "name": "p",
                "in": "header",
            }
        ]
    )