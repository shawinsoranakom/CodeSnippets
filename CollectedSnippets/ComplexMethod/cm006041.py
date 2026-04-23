def test_process_schema_missing_optional_keys_updated(self):
        schema = [
            {"name": "field1", "type": "str", "default": "default_value1"},
            {"name": "field2", "type": "int", "default": 0, "description": "Field 2 description"},
            {"name": "field3", "type": "list", "default": [], "multiple": True},
            {"name": "field4", "type": "dict", "default": {}, "description": "Field 4 description", "multiple": True},
        ]
        result_model = build_model_from_schema(schema)
        assert result_model.__annotations__["field1"] == str  # noqa: E721
        assert result_model.model_fields["field1"].description == ""
        assert result_model.__annotations__["field2"] == int  # noqa: E721
        assert result_model.model_fields["field2"].description == "Field 2 description"
        assert result_model.__annotations__["field3"] == list[list[Any]]
        assert result_model.model_fields["field3"].description == ""
        assert result_model.__annotations__["field4"] == list[dict[str, Any]]
        assert result_model.model_fields["field4"].description == "Field 4 description"