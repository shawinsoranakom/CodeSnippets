def test_extras_with_input_examples() -> None:
    """Test that extras with `input_examples` are merged into tool definitions."""

    @tool(
        extras={
            "input_examples": [
                {"location": "San Francisco, CA", "unit": "fahrenheit"},
                {"location": "Tokyo, Japan", "unit": "celsius"},
            ]
        }
    )
    def get_weather(location: str, unit: str = "fahrenheit") -> str:
        """Get weather for a location."""
        return f"Weather in {location}"

    model = ChatAnthropic(model=MODEL_NAME)  # type: ignore[call-arg]
    model_with_tools = model.bind_tools([get_weather])

    payload = model_with_tools._get_request_payload(  # type: ignore[attr-defined]
        "test",
        **model_with_tools.kwargs,  # type: ignore[attr-defined]
    )

    weather_tool = None
    for tool_def in payload["tools"]:
        if isinstance(tool_def, dict) and tool_def.get("name") == "get_weather":
            weather_tool = tool_def
            break

    assert weather_tool is not None
    assert "input_examples" in weather_tool
    assert len(weather_tool["input_examples"]) == 2
    assert weather_tool["input_examples"][0] == {
        "location": "San Francisco, CA",
        "unit": "fahrenheit",
    }

    # Beta header is required
    assert "betas" in payload
    assert "advanced-tool-use-2025-11-20" in payload["betas"]