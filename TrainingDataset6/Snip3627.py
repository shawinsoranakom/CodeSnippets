def test_schema(path: str, expected_name: str, expected_title: str):
    assert app.openapi()["paths"][path]["get"]["parameters"] == snapshot(
        [
            {
                "required": True,
                "schema": {"title": Is(expected_title), "type": "string"},
                "name": Is(expected_name),
                "in": "path",
            }
        ]
    )