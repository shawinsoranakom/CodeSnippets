def test_default_configuration(self):
        """Test default configuration values."""
        config = WebPlaywrightConfiguration()
        assert config.browser_type == "chromium"
        assert config.headless is True
        assert config.max_retries == 3
        assert config.page_load_timeout == 30000
        assert config.max_content_length == 100_000
        assert config.use_cloud_fallback is True
        assert config.block_resources is True