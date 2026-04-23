def test_merge_execution_input():
    # Test case for basic list extraction
    data = {
        "list_$_0": "a",
        "list_$_1": "b",
    }
    result = merge_execution_input(data)
    assert "list" in result
    assert result["list"] == ["a", "b"]

    # Test case for basic dict extraction
    data = {
        "dict_#_key1": "value1",
        "dict_#_key2": "value2",
    }
    result = merge_execution_input(data)
    assert "dict" in result
    assert result["dict"] == {"key1": "value1", "key2": "value2"}

    # Test case for object extraction
    class Sample:
        def __init__(self):
            self.attr1 = None
            self.attr2 = None

    data = {
        "object_@_attr1": "value1",
        "object_@_attr2": "value2",
    }
    result = merge_execution_input(data)
    assert "object" in result
    assert isinstance(result["object"], MockObject)
    assert result["object"].attr1 == "value1"
    assert result["object"].attr2 == "value2"

    # Test case for nested list extraction
    data = {
        "nested_list_$_0_$_0": "a",
        "nested_list_$_0_$_1": "b",
        "nested_list_$_1_$_0": "c",
    }
    result = merge_execution_input(data)
    assert "nested_list" in result
    assert result["nested_list"] == [["a", "b"], ["c"]]

    # Test case for list containing dict
    data = {
        "list_with_dict_$_0_#_key1": "value1",
        "list_with_dict_$_0_#_key2": "value2",
        "list_with_dict_$_1_#_key3": "value3",
    }
    result = merge_execution_input(data)
    assert "list_with_dict" in result
    assert result["list_with_dict"] == [
        {"key1": "value1", "key2": "value2"},
        {"key3": "value3"},
    ]

    # Test case for dict containing list
    data = {
        "dict_with_list_#_key1_$_0": "value1",
        "dict_with_list_#_key1_$_1": "value2",
        "dict_with_list_#_key2_$_0": "value3",
    }
    result = merge_execution_input(data)
    assert "dict_with_list" in result
    assert result["dict_with_list"] == {
        "key1": ["value1", "value2"],
        "key2": ["value3"],
    }

    # Test case for complex nested structure
    data = {
        "complex_$_0_#_key1_$_0": "value1",
        "complex_$_0_#_key1_$_1": "value2",
        "complex_$_0_#_key2_@_attr1": "value3",
        "complex_$_1_#_key3_$_0": "value4",
    }
    result = merge_execution_input(data)
    assert "complex" in result
    assert result["complex"][0]["key1"] == ["value1", "value2"]
    assert isinstance(result["complex"][0]["key2"], MockObject)
    assert result["complex"][0]["key2"].attr1 == "value3"
    assert result["complex"][1]["key3"] == ["value4"]

    # Test case for invalid list index
    data = {"list_$_invalid": "value"}
    with pytest.raises(ValueError, match="index must be an integer"):
        merge_execution_input(data)

    # Test cases for delimiter ordering
    # Test case 1: List -> Dict -> List
    data = {
        "nested_$_0_#_key_$_0": "value1",
        "nested_$_0_#_key_$_1": "value2",
    }
    result = merge_execution_input(data)
    assert "nested" in result
    assert result["nested"][0]["key"] == ["value1", "value2"]

    # Test case 2: Dict -> List -> Object
    data = {
        "nested_#_key_$_0_@_attr": "value1",
        "nested_#_key_$_1_@_attr": "value2",
    }
    result = merge_execution_input(data)
    assert "nested" in result
    assert isinstance(result["nested"]["key"][0], MockObject)
    assert result["nested"]["key"][0].attr == "value1"
    assert result["nested"]["key"][1].attr == "value2"

    # Test case 3: Object -> List -> Dict
    data = {
        "nested_@_items_$_0_#_key": "value1",
        "nested_@_items_$_1_#_key": "value2",
    }
    result = merge_execution_input(data)
    assert "nested" in result
    nested = result["nested"]
    assert isinstance(nested, MockObject)
    items = nested.items
    assert isinstance(items, list)
    assert items[0]["key"] == "value1"
    assert items[1]["key"] == "value2"

    # Test case 4: Complex nested structure with all types
    data = {
        "deep_#_key_$_0_@_data_$_0_#_items_$_0_#_value": "deep_value",
        "deep_#_key_$_0_@_data_$_1_#_items_$_0_#_value": "another_value",
    }
    result = merge_execution_input(data)
    assert "deep" in result
    deep_key = result["deep"]["key"][0]
    assert deep_key is not None
    data0 = getattr(deep_key, "data", None)
    assert isinstance(data0, list)
    # Check items0
    items0 = None
    if len(data0) > 0 and isinstance(data0[0], dict) and "items" in data0[0]:
        items0 = data0[0]["items"]
    assert isinstance(items0, list)
    items0 = cast(list, items0)
    assert len(items0) > 0
    assert isinstance(items0[0], dict)
    assert items0[0]["value"] == "deep_value"  # type: ignore
    # Check items1
    items1 = None
    if len(data0) > 1 and isinstance(data0[1], dict) and "items" in data0[1]:
        items1 = data0[1]["items"]
    assert isinstance(items1, list)
    items1 = cast(list, items1)
    assert len(items1) > 0
    assert isinstance(items1[0], dict)
    assert items1[0]["value"] == "another_value"  # type: ignore

    # Test case 5: Mixed delimiter types in different orders
    # the last one should replace the type
    data = {
        "mixed_$_0_#_key_@_attr": "value1",  # List -> Dict -> Object
        "mixed_#_key_$_0_@_attr": "value2",  # Dict -> List -> Object
        "mixed_@_attr_$_0_#_key": "value3",  # Object -> List -> Dict
    }
    result = merge_execution_input(data)
    assert "mixed" in result
    assert result["mixed"].attr[0]["key"] == "value3"