def test_func_call_tool_with_kwargs_schema_generation() -> None:
    """Test correct schema generation for a partial function with kwargs."""

    def get_weather(country: str, city: str) -> str:
        return f"The temperature in {city}, {country} is 75°"

    partial_function = partial(get_weather, country="Germany")
    tool = FunctionTool(partial_function, description="Partial function tool.")
    schema = tool.schema

    assert schema["name"] == "get_weather"
    assert "description" in schema
    assert schema["description"] == "Partial function tool."
    assert "parameters" in schema
    assert schema["parameters"]["type"] == "object"
    assert schema["parameters"]["properties"].keys() == {"country", "city"}
    assert schema["parameters"]["properties"]["city"]["type"] == "string"
    assert schema["parameters"]["properties"]["country"]["type"] == "string"
    assert "required" in schema["parameters"]
    assert schema["parameters"]["required"] == ["city"]  # only city is required
    assert len(schema["parameters"]["properties"]) == 2