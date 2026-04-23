def test_mixed_data_types_analysis(self):
        """Test analysis of mixed data types."""
        mixed_data = {
            "strings": ["hello", "world"],
            "numbers": [1, 2, 3.14, 5],
            "booleans": [True, False, True],
            "mixed_list": [1, "hello", True, None, {"nested": "value"}],
            "json_strings": ['{"key": "value"}', '{"another": "json"}'],
            "dates": ["has date in string", "another time value"],
            "empty_structures": {"empty_list": [], "empty_dict": {}},
        }

        result = get_data_structure(mixed_data)
        structure = result["structure"]

        assert "list(str)" in structure["strings"]
        assert "int|float" in structure["numbers"] or "float|int" in structure["numbers"]
        assert "list(bool)" in structure["booleans"]
        # The mixed list types may be in any order, so just check it contains list() and multiple types
        mixed_list_str = structure["mixed_list"]
        assert "list(" in mixed_list_str
        assert "|" in mixed_list_str  # Multiple types indicated by pipe
        assert "str(json)" in structure["json_strings"]
        assert "str(possible_date)" in structure["dates"]
        assert structure["empty_structures"]["empty_list"] == "list(unknown)"
        assert structure["empty_structures"]["empty_dict"] == {}