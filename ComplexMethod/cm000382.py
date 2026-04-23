def test_parse_execution_output():
    # Test case for basic output
    output = ("result", "value")
    assert parse_execution_output(output, "result") == "value"

    # Test case for list output
    output = ("result", [10, 20, 30])
    assert parse_execution_output(output, "result_$_1") == 20

    # Test case for dict output
    output = ("result", {"key1": "value1", "key2": "value2"})
    assert parse_execution_output(output, "result_#_key1") == "value1"

    # Test case for object output
    class Sample:
        def __init__(self):
            self.attr1 = "value1"
            self.attr2 = "value2"

    output = ("result", Sample())
    assert parse_execution_output(output, "result_@_attr1") == "value1"

    # Test case for nested list output
    output = ("result", [[1, 2], [3, 4]])
    assert parse_execution_output(output, "result_$_0_$_1") == 2
    assert parse_execution_output(output, "result_$_1_$_0") == 3

    # Test case for list containing dict
    output = ("result", [{"key1": "value1"}, {"key2": "value2"}])
    assert parse_execution_output(output, "result_$_0_#_key1") == "value1"
    assert parse_execution_output(output, "result_$_1_#_key2") == "value2"

    # Test case for dict containing list
    output = ("result", {"key1": [1, 2], "key2": [3, 4]})
    assert parse_execution_output(output, "result_#_key1_$_1") == 2
    assert parse_execution_output(output, "result_#_key2_$_0") == 3

    # Test case for complex nested structure
    class NestedSample:
        def __init__(self):
            self.attr1 = [1, 2]
            self.attr2 = {"key": "value"}

    output = ("result", [NestedSample(), {"key": [1, 2]}])
    assert parse_execution_output(output, "result_$_0_@_attr1_$_1") == 2
    assert parse_execution_output(output, "result_$_0_@_attr2_#_key") == "value"
    assert parse_execution_output(output, "result_$_1_#_key_$_0") == 1

    # Test case for non-existent paths
    output = ("result", [1, 2, 3])
    assert parse_execution_output(output, "result_$_5") is None
    assert parse_execution_output(output, "result_#_key") is None
    assert parse_execution_output(output, "result_@_attr") is None
    assert parse_execution_output(output, "wrong_name") is None

    # Test cases for delimiter processing order
    # Test case 1: List -> Dict -> List
    output = ("result", [[{"key": [1, 2]}], [3, 4]])
    assert parse_execution_output(output, "result_$_0_$_0_#_key_$_1") == 2

    # Test case 2: Dict -> List -> Object
    class NestedObj:
        def __init__(self):
            self.value = "nested"

    output = ("result", {"key": [NestedObj(), 2]})
    assert parse_execution_output(output, "result_#_key_$_0_@_value") == "nested"

    # Test case 3: Object -> List -> Dict
    class ParentObj:
        def __init__(self):
            self.items = [{"nested": "value"}]

    output = ("result", ParentObj())
    assert parse_execution_output(output, "result_@_items_$_0_#_nested") == "value"

    # Test case 4: Complex nested structure with all types
    class ComplexObj:
        def __init__(self):
            self.data = [{"items": [{"value": "deep"}]}]

    output = ("result", {"key": [ComplexObj()]})
    assert (
        parse_execution_output(
            output, "result_#_key_$_0_@_data_$_0_#_items_$_0_#_value"
        )
        == "deep"
    )

    # Test case 5: Invalid paths that should return None
    output = ("result", [{"key": [1, 2]}])
    assert parse_execution_output(output, "result_$_0_#_wrong_key") is None
    assert parse_execution_output(output, "result_$_0_#_key_$_5") is None
    assert parse_execution_output(output, "result_$_0_@_attr") is None

    # Test case 6: Mixed delimiter types in wrong order
    output = ("result", {"key": [1, 2]})
    assert (
        parse_execution_output(output, "result_#_key_$_1_@_attr") is None
    )  # Should fail at @_attr
    assert (
        parse_execution_output(output, "result_@_attr_$_0_#_key") is None
    )  # Should fail at @_attr

    # Test case 7: Tool pin routing with matching node ID and pin name
    output = ("tools_^_node123_~_query", "search term")
    assert parse_execution_output(output, "tools", "node123", "query") == "search term"

    # Test case 8: Tool pin routing with node ID mismatch
    output = ("tools_^_node123_~_query", "search term")
    assert parse_execution_output(output, "tools", "node456", "query") is None

    # Test case 9: Tool pin routing with pin name mismatch
    output = ("tools_^_node123_~_query", "search term")
    assert parse_execution_output(output, "tools", "node123", "different_pin") is None

    # Test case 10: Tool pin routing with complex field names
    output = ("tools_^_node789_~_nested_field", {"key": "value"})
    result = parse_execution_output(output, "tools", "node789", "nested_field")
    assert result == {"key": "value"}

    # Test case 11: Tool pin routing missing required parameters should raise error
    output = ("tools_^_node123_~_query", "search term")
    try:
        parse_execution_output(output, "tools", "node123")  # Missing sink_pin_name
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "must be provided for tool pin routing" in str(e)

    # Test case 12: Non-tool pin with similar pattern should use normal logic
    output = ("tools_^_node123_~_query", "search term")
    assert parse_execution_output(output, "different_name", "node123", "query") is None