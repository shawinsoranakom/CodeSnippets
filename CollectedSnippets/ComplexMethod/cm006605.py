def test_schema_to_langflow_inputs_preserves_optional_defaults_and_nullable_objects():
    schema = {
        "type": "object",
        "properties": {
            "task": {"type": "string"},
            "model": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": "claude-sonnet-4.6",
            },
            "keep_alive": {
                "anyOf": [{"type": "boolean"}, {"type": "null"}],
                "default": False,
            },
            "output_schema": {
                "anyOf": [{"type": "object"}, {"type": "null"}],
                "default": None,
            },
            "proxy_country": {
                "anyOf": [{"type": "string"}, {"type": "null"}],
                "default": "us",
            },
        },
        "required": ["task"],
    }
    model = create_input_schema_from_json_schema(schema)

    inputs = {input_.name: input_ for input_ in schema_to_langflow_inputs(model)}

    assert isinstance(inputs["task"], MessageTextInput)
    assert inputs["task"].required is True
    assert inputs["task"].value == ""

    assert isinstance(inputs["model"], MessageTextInput)
    assert inputs["model"].value == "claude-sonnet-4.6"

    assert isinstance(inputs["keep_alive"], BoolInput)
    assert inputs["keep_alive"].value is False

    assert isinstance(inputs["output_schema"], NestedDictInput)
    assert inputs["output_schema"].required is False
    assert inputs["output_schema"].value is None

    assert isinstance(inputs["proxy_country"], MessageTextInput)
    assert inputs["proxy_country"].value == "us"