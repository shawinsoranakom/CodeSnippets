def test_custom_configuration(self):
        """Test custom configuration values."""
        config = WebPlaywrightConfiguration(
            browser_type="firefox",
            headless=False,
            max_retries=5,
            page_load_timeout=60000,
            max_content_length=50_000,
            use_cloud_fallback=False,
            proxy="http://proxy:8080",
        )
        assert config.browser_type == "firefox"
        assert config.headless is False
        assert config.max_retries == 5
        assert config.page_load_timeout == 60000
        assert config.max_content_length == 50_000
        assert config.use_cloud_fallback is False
        assert config.proxy == "http://proxy:8080"