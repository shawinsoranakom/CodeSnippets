def test_dict_input(self):
        """Test with dictionary as input."""
        test_dict = {
            "name": "Test",
            "count": 42,
            "items": [1, 2, 3],
            "metadata": {
                "created": "date created on server",  # Contains "date" pattern
                "tags": ["tag1", "tag2"],
            },
        }

        result = get_data_structure(test_dict)

        assert "structure" in result
        structure = result["structure"]
        assert structure["name"] == "str"
        assert structure["count"] == "int"
        assert "list(int)" in structure["items"]
        assert isinstance(structure["metadata"], dict)
        assert "str(possible_date)" in structure["metadata"]["created"]
        assert "list(str)" in structure["metadata"]["tags"]