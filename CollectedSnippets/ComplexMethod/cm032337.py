def test_provider_initialization(self):
        """Test provider initialization."""
        provider = AliyunCodeInterpreterProvider()

        assert provider.access_key_id == ""
        assert provider.access_key_secret == ""
        assert provider.account_id == ""
        assert provider.region == "cn-hangzhou"
        assert provider.template_name == ""
        assert provider.timeout == 30
        assert not provider._initialized