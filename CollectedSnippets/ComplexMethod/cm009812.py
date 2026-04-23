def test_stringify_value_nested_structures() -> None:
    """Test stringifying nested structures."""
    # Test nested dict in list
    nested_data = {
        "users": [
            {"name": "Alice", "age": 25},
            {"name": "Bob", "age": 30},
        ],
        "metadata": {"total_users": 2, "active": True},
    }

    result = stringify_value(nested_data)

    # Should contain all the nested values
    assert "users:" in result
    assert "name: Alice" in result
    assert "name: Bob" in result
    assert "metadata:" in result
    assert "total_users: 2" in result
    assert "active: True" in result

    # Test list of mixed types
    mixed_list = ["string", 42, {"key": "value"}, ["nested", "list"]]
    result = stringify_value(mixed_list)

    assert "string" in result
    assert "42" in result
    assert "key: value" in result
    assert "nested" in result
    assert "list" in result