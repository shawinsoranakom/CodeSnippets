def test_array_items_with_object_schema_properties() -> None:
    """Test that array items with object schemas create proper Pydantic models."""
    schema = {
        "type": "object",
        "properties": {
            "users": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}, "email": {"type": "string"}, "age": {"type": "integer"}},
                    "required": ["name", "email"],
                },
            }
        },
    }

    converter = _JSONSchemaToPydantic()
    Model = converter.json_schema_to_pydantic(schema, "UserListModel")

    # Verify the users field has correct type annotation
    users_field = Model.model_fields["users"]
    from typing import Union, get_args, get_origin

    # Extract inner type from Optional[List[...]]
    actual_list_type = users_field.annotation
    if get_origin(users_field.annotation) is Union:
        union_args = get_args(users_field.annotation)
        for arg in union_args:
            if get_origin(arg) is list:
                actual_list_type = arg
                break

    assert get_origin(actual_list_type) is list
    inner_type = get_args(actual_list_type)[0]

    # Verify array items are BaseModel subclasses, not dict
    assert inner_type is not dict
    assert hasattr(inner_type, "model_fields")

    # Verify expected fields are present
    expected_fields = {"name", "email", "age"}
    actual_fields = set(inner_type.model_fields.keys())
    assert expected_fields.issubset(actual_fields)

    # Test instantiation and field access
    test_data = {
        "users": [
            {"name": "Alice", "email": "alice@example.com", "age": 30},
            {"name": "Bob", "email": "bob@example.com"},
        ]
    }

    instance = Model(**test_data)
    assert len(instance.users) == 2  # type: ignore[attr-defined]

    first_user = instance.users[0]  # type: ignore[attr-defined]
    assert hasattr(first_user, "model_fields")  # type: ignore[reportUnknownArgumentType]
    assert not isinstance(first_user, dict)

    # Test attribute access (BaseModel behavior)
    assert first_user.name == "Alice"  # type: ignore[attr-defined]
    assert first_user.email == "alice@example.com"  # type: ignore[attr-defined]
    assert first_user.age == 30