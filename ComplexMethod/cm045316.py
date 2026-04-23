def test_func_tool_with_partial_positional_arguments_schema_generation() -> None:
    """Test correct schema generation for a partial function with positional arguments."""

    def get_weather(country: str, city: str) -> str:
        return f"The temperature in {city}, {country} is 75°"

    partial_function = partial(get_weather, "Germany")
    tool = FunctionTool(partial_function, description="Partial function tool.")
    schema = tool.schema

    assert schema["name"] == "get_weather"
    assert "description" in schema
    assert schema["description"] == "Partial function tool."
    assert "parameters" in schema
    assert schema["parameters"]["type"] == "object"
    assert schema["parameters"]["properties"].keys() == {"city"}
    assert schema["parameters"]["properties"]["city"]["type"] == "string"
    assert schema["parameters"]["properties"]["city"]["description"] == "city"
    assert "required" in schema["parameters"]
    assert schema["parameters"]["required"] == ["city"]
    assert "country" not in schema["parameters"]["properties"]  # check country not in schema params
    assert len(schema["parameters"]["properties"]) == 1