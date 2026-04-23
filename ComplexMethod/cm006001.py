def test_should_have_schema_with_table_schema(self):
        """Test that schema input has table_schema defined."""
        schema_input = next((i for i in AreduceComponent.inputs if i.name == "schema"), None)
        assert schema_input is not None
        assert schema_input.table_schema is not None
        assert len(schema_input.table_schema) > 0

        field_names = {field["name"] for field in schema_input.table_schema}
        assert "name" in field_names
        assert "description" in field_names
        assert "type" in field_names
        assert "multiple" in field_names