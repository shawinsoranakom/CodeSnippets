def test_get_config_schema(self):
        """Test getting configuration schema."""
        schema = SelfManagedProvider.get_config_schema()

        assert "endpoint" in schema
        assert schema["endpoint"]["type"] == "string"
        assert schema["endpoint"]["required"] is True
        assert schema["endpoint"]["default"] == "http://localhost:9385"

        assert "timeout" in schema
        assert schema["timeout"]["type"] == "integer"
        assert schema["timeout"]["default"] == 30

        assert "max_retries" in schema
        assert schema["max_retries"]["type"] == "integer"

        assert "pool_size" in schema
        assert schema["pool_size"]["type"] == "integer"