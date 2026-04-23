def test_convert_param_value_single_types(parser):
    """Test _convert_param_value with single type parameters."""
    # Test string type
    assert parser._convert_param_value("hello", "string") == "hello"
    assert parser._convert_param_value("123", "string") == "123"

    # Test integer type - valid integers
    assert parser._convert_param_value("123", "integer") == 123
    assert parser._convert_param_value("456", "int") == 456
    # Invalid integer should return original string (due to exception catch)
    assert parser._convert_param_value("abc", "integer") == "abc"

    # Test float/number type
    assert parser._convert_param_value("123.45", "float") == 123.45
    assert (
        parser._convert_param_value("123.0", "number") == 123
    )  # Should be int when whole number
    assert parser._convert_param_value("123.5", "number") == 123.5
    # Invalid float should return original string
    assert parser._convert_param_value("abc", "float") == "abc"

    # Test boolean type - valid boolean values
    assert parser._convert_param_value("true", "boolean") is True
    assert parser._convert_param_value("false", "bool") is False
    assert parser._convert_param_value("1", "boolean") is True
    assert parser._convert_param_value("0", "boolean") is False
    # Invalid boolean should return original string
    assert parser._convert_param_value("yes", "boolean") == "yes"
    assert parser._convert_param_value("no", "bool") == "no"

    # Test null value
    assert parser._convert_param_value("null", "string") is None
    assert parser._convert_param_value("null", "integer") is None

    # Test object/array type (JSON)
    assert parser._convert_param_value('{"key": "value"}', "object") == {"key": "value"}
    assert parser._convert_param_value("[1, 2, 3]", "array") == [1, 2, 3]
    # Invalid JSON should return original string
    assert parser._convert_param_value("{invalid}", "object") == "{invalid}"

    # Test fallback for unknown type (tries json.loads, then returns original)
    assert parser._convert_param_value('{"key": "value"}', "unknown") == {
        "key": "value"
    }
    assert parser._convert_param_value("plain text", "unknown") == "plain text"