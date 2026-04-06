def test_required_list_str_schema(path: str):
    openapi = app.openapi()
    body_model_name = get_body_model_name(openapi, path)

    assert app.openapi()["components"]["schemas"][body_model_name] == {
        "properties": {
            "p": {
                "items": {"type": "string"},
                "title": "P",
                "type": "array",
            },
        },
        "required": ["p"],
        "title": body_model_name,
        "type": "object",
    }