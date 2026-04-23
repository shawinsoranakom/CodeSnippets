def test_json_schema_alias_functionality(self):
        """Test that JSON schema creation includes aliases for camelCase field names."""
        from lfx.schema.json_schema import create_input_schema_from_json_schema
        from pydantic import ValidationError

        # Create a JSON schema with snake_case field names
        test_schema = {
            "type": "object",
            "properties": {
                "weather_main": {"type": "string", "description": "Main weather condition"},
                "top_n": {"type": "integer", "description": "Number of results"},
                "user_id": {"type": "string", "description": "User identifier"},
            },
            "required": ["weather_main", "top_n"],
        }

        # Create the Pydantic model using our function
        input_schema = create_input_schema_from_json_schema(test_schema)

        # Test with snake_case field names (should work)
        result1 = input_schema(weather_main="Rain", top_n=8)
        assert result1.weather_main == "Rain"
        assert result1.top_n == 8

        # Test with camelCase field names (should also work due to aliases)
        result2 = input_schema(weatherMain="Rain", topN=8)
        assert result2.weather_main == "Rain"
        assert result2.top_n == 8

        # Test with mixed case field names (should work)
        result3 = input_schema(weatherMain="Rain", top_n=8, userId="user123")
        assert result3.weather_main == "Rain"
        assert result3.top_n == 8
        assert result3.user_id == "user123"

        # Test validation error (should fail with missing required field)
        with pytest.raises(ValidationError):
            input_schema(weatherMain="Rain")