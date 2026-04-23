def test_pydantic_tools_parser_with_nested_models() -> None:
    """Test PydanticToolsParser with nested Pydantic v1 and v2 models."""
    # Nested v1 models
    if sys.version_info >= (3, 14):
        AddressV1 = pydantic.v1.create_model(  # noqa: N806
            "AddressV1",
            __doc__="Address using Pydantic v1.",
            street=(str, ...),
            city=(str, ...),
            zip_code=(str, ...),
        )
        PersonV1 = pydantic.v1.create_model(  # noqa: N806
            "PersonV1",
            __doc__="Person with nested address using Pydantic v1.",
            name=(str, ...),
            age=(int, ...),
            address=(AddressV1, ...),
        )
    else:

        class AddressV1(pydantic.v1.BaseModel):
            """Address using Pydantic v1."""

            street: str
            city: str
            zip_code: str

        class PersonV1(pydantic.v1.BaseModel):
            """Person with nested address using Pydantic v1."""

            name: str
            age: int
            address: AddressV1

    # Nested v2 models
    class CoordinatesV2(BaseModel):
        """Coordinates using Pydantic v2."""

        latitude: float
        longitude: float

    class LocationV2(BaseModel):
        """Location with nested coordinates using Pydantic v2."""

        name: str
        coordinates: CoordinatesV2

    # Test with nested Pydantic v1 model
    parser_v1 = PydanticToolsParser(tools=[PersonV1])
    message_v1 = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_person",
                "name": "PersonV1",
                "args": {
                    "name": "Alice",
                    "age": 30,
                    "address": {
                        "street": "123 Main St",
                        "city": "Springfield",
                        "zip_code": "12345",
                    },
                },
            }
        ],
    )
    generation_v1 = ChatGeneration(message=message_v1)
    result_v1 = parser_v1.parse_result([generation_v1])

    assert len(result_v1) == 1
    assert isinstance(result_v1[0], PersonV1)
    assert result_v1[0].name == "Alice"  # type: ignore[attr-defined,unused-ignore]
    assert result_v1[0].age == 30  # type: ignore[attr-defined,unused-ignore]
    assert isinstance(result_v1[0].address, AddressV1)  # type: ignore[attr-defined,unused-ignore]
    assert result_v1[0].address.street == "123 Main St"  # type: ignore[attr-defined,unused-ignore]
    assert result_v1[0].address.city == "Springfield"  # type: ignore[attr-defined,unused-ignore]

    # Test with nested Pydantic v2 model
    parser_v2 = PydanticToolsParser(tools=[LocationV2])
    message_v2 = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_location",
                "name": "LocationV2",
                "args": {
                    "name": "Eiffel Tower",
                    "coordinates": {"latitude": 48.8584, "longitude": 2.2945},
                },
            }
        ],
    )
    generation_v2 = ChatGeneration(message=message_v2)
    result_v2 = parser_v2.parse_result([generation_v2])

    assert len(result_v2) == 1
    assert isinstance(result_v2[0], LocationV2)
    assert result_v2[0].name == "Eiffel Tower"
    assert isinstance(result_v2[0].coordinates, CoordinatesV2)
    assert result_v2[0].coordinates.latitude == 48.8584
    assert result_v2[0].coordinates.longitude == 2.2945

    # Test with both nested models in one message
    parser_mixed = PydanticToolsParser(tools=[PersonV1, LocationV2])
    message_mixed = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_person",
                "name": "PersonV1",
                "args": {
                    "name": "Bob",
                    "age": 25,
                    "address": {
                        "street": "456 Oak Ave",
                        "city": "Portland",
                        "zip_code": "97201",
                    },
                },
            },
            {
                "id": "call_location",
                "name": "LocationV2",
                "args": {
                    "name": "Golden Gate Bridge",
                    "coordinates": {"latitude": 37.8199, "longitude": -122.4783},
                },
            },
        ],
    )
    generation_mixed = ChatGeneration(message=message_mixed)
    result_mixed = parser_mixed.parse_result([generation_mixed])

    assert len(result_mixed) == 2
    assert isinstance(result_mixed[0], PersonV1)
    assert result_mixed[0].name == "Bob"  # type: ignore[attr-defined,unused-ignore]
    assert result_mixed[0].address.city == "Portland"  # type: ignore[attr-defined,unused-ignore]
    assert isinstance(result_mixed[1], LocationV2)
    assert result_mixed[1].name == "Golden Gate Bridge"
    assert result_mixed[1].coordinates.latitude == 37.8199