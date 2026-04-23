def test_pydantic_tools_parser_with_mixed_pydantic_versions() -> None:
    """Test PydanticToolsParser with both Pydantic v1 and v2 models."""
    # For Python 3.14+ compatibility, use create_model for Pydantic v1
    if sys.version_info >= (3, 14):
        WeatherV1 = pydantic.v1.create_model(  # noqa: N806
            "WeatherV1",
            __doc__="Weather information using Pydantic v1.",
            temperature=(int, ...),
            conditions=(str, ...),
        )
    else:

        class WeatherV1(pydantic.v1.BaseModel):
            """Weather information using Pydantic v1."""

            temperature: int
            conditions: str

    class LocationV2(BaseModel):
        """Location information using Pydantic v2."""

        city: str
        country: str

    # Test with Pydantic v1 model
    parser_v1 = PydanticToolsParser(tools=[WeatherV1])
    message_v1 = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_weather",
                "name": "WeatherV1",
                "args": {"temperature": 25, "conditions": "sunny"},
            }
        ],
    )
    generation_v1 = ChatGeneration(message=message_v1)
    result_v1 = parser_v1.parse_result([generation_v1])

    assert len(result_v1) == 1
    assert isinstance(result_v1[0], WeatherV1)
    assert result_v1[0].temperature == 25  # type: ignore[attr-defined,unused-ignore]
    assert result_v1[0].conditions == "sunny"  # type: ignore[attr-defined,unused-ignore]

    # Test with Pydantic v2 model
    parser_v2 = PydanticToolsParser(tools=[LocationV2])
    message_v2 = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_location",
                "name": "LocationV2",
                "args": {"city": "Paris", "country": "France"},
            }
        ],
    )
    generation_v2 = ChatGeneration(message=message_v2)
    result_v2 = parser_v2.parse_result([generation_v2])

    assert len(result_v2) == 1
    assert isinstance(result_v2[0], LocationV2)
    assert result_v2[0].city == "Paris"
    assert result_v2[0].country == "France"

    # Test with both v1 and v2 models
    parser_mixed = PydanticToolsParser(tools=[WeatherV1, LocationV2])
    message_mixed = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_weather",
                "name": "WeatherV1",
                "args": {"temperature": 20, "conditions": "cloudy"},
            },
            {
                "id": "call_location",
                "name": "LocationV2",
                "args": {"city": "London", "country": "UK"},
            },
        ],
    )
    generation_mixed = ChatGeneration(message=message_mixed)
    result_mixed = parser_mixed.parse_result([generation_mixed])

    assert len(result_mixed) == 2
    assert isinstance(result_mixed[0], WeatherV1)
    assert result_mixed[0].temperature == 20  # type: ignore[attr-defined,unused-ignore]
    assert isinstance(result_mixed[1], LocationV2)
    assert result_mixed[1].city == "London"