def test_get_config_schema(self):
        """Test getting configuration schema."""
        schema = AliyunCodeInterpreterProvider.get_config_schema()

        assert "access_key_id" in schema
        assert schema["access_key_id"]["required"] is True

        assert "access_key_secret" in schema
        assert schema["access_key_secret"]["required"] is True

        assert "account_id" in schema
        assert schema["account_id"]["required"] is True

        assert "region" in schema
        assert "template_name" in schema
        assert "timeout" in schema