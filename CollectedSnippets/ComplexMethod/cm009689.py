def test_pydantic_tools_parser_with_optional_fields() -> None:
    """Test PydanticToolsParser with optional fields in v1 and v2 models."""
    if sys.version_info >= (3, 14):
        ProductV1 = pydantic.v1.create_model(  # noqa: N806
            "ProductV1",
            __doc__="Product with optional fields using Pydantic v1.",
            name=(str, ...),
            price=(float, ...),
            description=(str | None, None),
            stock=(int, 0),
        )
    else:

        class ProductV1(pydantic.v1.BaseModel):
            """Product with optional fields using Pydantic v1."""

            name: str
            price: float
            description: str | None = None
            stock: int = 0

    # v2 model with optional fields
    class UserV2(BaseModel):
        """User with optional fields using Pydantic v2."""

        username: str
        email: str
        bio: str | None = None
        age: int | None = None

    # Test v1 with all fields provided
    parser_v1_full = PydanticToolsParser(tools=[ProductV1])
    message_v1_full = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_product_full",
                "name": "ProductV1",
                "args": {
                    "name": "Laptop",
                    "price": 999.99,
                    "description": "High-end laptop",
                    "stock": 50,
                },
            }
        ],
    )
    generation_v1_full = ChatGeneration(message=message_v1_full)
    result_v1_full = parser_v1_full.parse_result([generation_v1_full])

    assert len(result_v1_full) == 1
    assert isinstance(result_v1_full[0], ProductV1)
    assert result_v1_full[0].name == "Laptop"  # type: ignore[attr-defined,unused-ignore]
    assert result_v1_full[0].price == 999.99  # type: ignore[attr-defined,unused-ignore]
    assert result_v1_full[0].description == "High-end laptop"  # type: ignore[attr-defined,unused-ignore]
    assert result_v1_full[0].stock == 50  # type: ignore[attr-defined,unused-ignore]

    # Test v1 with only required fields
    parser_v1_minimal = PydanticToolsParser(tools=[ProductV1])
    message_v1_minimal = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_product_minimal",
                "name": "ProductV1",
                "args": {"name": "Mouse", "price": 29.99},
            }
        ],
    )
    generation_v1_minimal = ChatGeneration(message=message_v1_minimal)
    result_v1_minimal = parser_v1_minimal.parse_result([generation_v1_minimal])

    assert len(result_v1_minimal) == 1
    assert isinstance(result_v1_minimal[0], ProductV1)
    assert result_v1_minimal[0].name == "Mouse"  # type: ignore[attr-defined,unused-ignore]
    assert result_v1_minimal[0].price == 29.99  # type: ignore[attr-defined,unused-ignore]
    assert result_v1_minimal[0].description is None  # type: ignore[attr-defined,unused-ignore]
    assert result_v1_minimal[0].stock == 0  # type: ignore[attr-defined,unused-ignore]

    # Test v2 with all fields provided
    parser_v2_full = PydanticToolsParser(tools=[UserV2])
    message_v2_full = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_user_full",
                "name": "UserV2",
                "args": {
                    "username": "john_doe",
                    "email": "john@example.com",
                    "bio": "Software developer",
                    "age": 28,
                },
            }
        ],
    )
    generation_v2_full = ChatGeneration(message=message_v2_full)
    result_v2_full = parser_v2_full.parse_result([generation_v2_full])

    assert len(result_v2_full) == 1
    assert isinstance(result_v2_full[0], UserV2)
    assert result_v2_full[0].username == "john_doe"
    assert result_v2_full[0].email == "john@example.com"
    assert result_v2_full[0].bio == "Software developer"
    assert result_v2_full[0].age == 28

    # Test v2 with only required fields
    parser_v2_minimal = PydanticToolsParser(tools=[UserV2])
    message_v2_minimal = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_user_minimal",
                "name": "UserV2",
                "args": {"username": "jane_smith", "email": "jane@example.com"},
            }
        ],
    )
    generation_v2_minimal = ChatGeneration(message=message_v2_minimal)
    result_v2_minimal = parser_v2_minimal.parse_result([generation_v2_minimal])

    assert len(result_v2_minimal) == 1
    assert isinstance(result_v2_minimal[0], UserV2)
    assert result_v2_minimal[0].username == "jane_smith"
    assert result_v2_minimal[0].email == "jane@example.com"
    assert result_v2_minimal[0].bio is None
    assert result_v2_minimal[0].age is None

    # Test mixed v1 and v2 with partial optional fields
    parser_mixed = PydanticToolsParser(tools=[ProductV1, UserV2])
    message_mixed = AIMessage(
        content="",
        tool_calls=[
            {
                "id": "call_product",
                "name": "ProductV1",
                "args": {"name": "Keyboard", "price": 79.99, "stock": 100},
            },
            {
                "id": "call_user",
                "name": "UserV2",
                "args": {
                    "username": "alice",
                    "email": "alice@example.com",
                    "age": 35,
                },
            },
        ],
    )
    generation_mixed = ChatGeneration(message=message_mixed)
    result_mixed = parser_mixed.parse_result([generation_mixed])

    assert len(result_mixed) == 2
    assert isinstance(result_mixed[0], ProductV1)
    assert result_mixed[0].name == "Keyboard"  # type: ignore[attr-defined,unused-ignore]
    assert result_mixed[0].description is None  # type: ignore[attr-defined,unused-ignore]
    assert result_mixed[0].stock == 100  # type: ignore[attr-defined,unused-ignore]
    assert isinstance(result_mixed[1], UserV2)
    assert result_mixed[1].username == "alice"
    assert result_mixed[1].bio is None
    assert result_mixed[1].age == 35