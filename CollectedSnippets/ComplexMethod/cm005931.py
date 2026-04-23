def test_load_table_data_with_dict_rows(self):
        """Test loading table data when rows are dictionaries."""
        component = TableSchemaDemoComponent()
        component.table_data = [
            {"username": "admin", "email": "admin@example.com", "role": "admin", "active": True},
            {"username": "user1", "email": "user1@example.com", "role": "user", "active": True},
        ]

        result = component.load_table_data()

        assert isinstance(result, list)
        assert len(result) == 2
        assert all(isinstance(item, Data) for item in result)

        # Check the data content
        assert result[0].data["username"] == "admin"
        assert result[0].data["email"] == "admin@example.com"
        assert result[1].data["username"] == "user1"
        assert result[1].data["email"] == "user1@example.com"