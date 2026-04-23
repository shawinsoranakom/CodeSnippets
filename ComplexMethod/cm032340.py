def test_aliyun_provider_has_abstract_methods(self):
        """Test that AliyunCodeInterpreterProvider implements all abstract methods."""
        provider = AliyunCodeInterpreterProvider()

        assert hasattr(provider, "initialize")
        assert callable(provider.initialize)

        assert hasattr(provider, "create_instance")
        assert callable(provider.create_instance)

        assert hasattr(provider, "execute_code")
        assert callable(provider.execute_code)

        assert hasattr(provider, "destroy_instance")
        assert callable(provider.destroy_instance)

        assert hasattr(provider, "health_check")
        assert callable(provider.health_check)

        assert hasattr(provider, "get_supported_languages")
        assert callable(provider.get_supported_languages)