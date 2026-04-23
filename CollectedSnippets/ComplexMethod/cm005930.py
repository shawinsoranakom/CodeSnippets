def test_load_table_data_with_mixed_types(self):
        """Test loading table data with mixed types (string, etc.)."""
        component = TableSchemaDemoComponent()
        component.table_data = [{"username": "admin"}, "user_string", 123]

        result = component.load_table_data()

        assert isinstance(result, list)
        assert len(result) == 3
        assert all(isinstance(item, Data) for item in result)

        # First item should be a dict
        assert result[0].data["username"] == "admin"

        # Second item should be converted to Data with row/index
        assert result[1].data["row"] == "user_string"
        assert result[1].data["index"] == 1

        # Third item should be converted to Data with row/index
        assert result[2].data["row"] == "123"
        assert result[2].data["index"] == 2