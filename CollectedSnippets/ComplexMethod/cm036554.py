def test_convert_param_value_multi_typed_values(parser):
    """Test _convert_param_value with multi-typed values (list of types)."""
    # Test with list of types where first type succeeds
    assert parser._convert_param_value("123", ["integer", "string"]) == 123
    assert parser._convert_param_value("true", ["boolean", "string"]) is True
    assert parser._convert_param_value('{"x": 1}', ["object", "string"]) == {"x": 1}

    # Test with list of types where first type fails but second succeeds
    # "abc" is not a valid integer, so should try string next
    assert parser._convert_param_value("abc", ["integer", "string"]) == "abc"

    # Test with list of types where all fail - should return original value
    # "invalid json" is not valid JSON, last type is "object" which will fail JSON parse
    result = parser._convert_param_value("invalid json", ["integer", "object"])
    assert result == "invalid json"  # Returns original value after all types fail

    # Test with three types
    assert parser._convert_param_value("123.5", ["integer", "float", "string"]) == 123.5
    assert parser._convert_param_value("true", ["integer", "boolean", "string"]) is True

    # Test with null in multi-type list
    assert parser._convert_param_value("null", ["integer", "string"]) is None
    assert parser._convert_param_value("null", ["boolean", "object"]) is None

    # Test nested type conversion - boolean fails, integer succeeds
    value = parser._convert_param_value("123", ["boolean", "integer", "string"])
    assert value == 123  # Should be integer, not boolean

    # Test that order matters
    assert (
        parser._convert_param_value("123", ["string", "integer"]) == "123"
    )  # String first
    assert (
        parser._convert_param_value("123", ["integer", "string"]) == 123
    )  # Integer first

    # Test with all types failing - returns original value
    assert (
        parser._convert_param_value("not_a_number", ["integer", "float", "boolean"])
        == "not_a_number"
    )