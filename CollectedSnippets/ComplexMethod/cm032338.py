def test_initialize_success(self, mock_template):
        """Test successful initialization."""
        # Mock health check response
        mock_template.list.return_value = []

        provider = AliyunCodeInterpreterProvider()
        result = provider.initialize(
            {
                "access_key_id": "LTAI5tXXXXXXXXXX",
                "access_key_secret": "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX",
                "account_id": "1234567890123456",
                "region": "cn-hangzhou",
                "template_name": "python-sandbox",
                "timeout": 20,
            }
        )

        assert result is True
        assert provider.access_key_id == "LTAI5tXXXXXXXXXX"
        assert provider.access_key_secret == "XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX"
        assert provider.account_id == "1234567890123456"
        assert provider.region == "cn-hangzhou"
        assert provider.template_name == "python-sandbox"
        assert provider.timeout == 20
        assert provider._initialized