def test_creates_valid_config_structure(self):
        """Config should have required logging configuration keys."""
        config = create_uvicorn_log_config(excluded_paths=["/health"])

        assert "version" in config
        assert config["version"] == 1
        assert "disable_existing_loggers" in config
        assert "formatters" in config
        assert "handlers" in config
        assert "loggers" in config
        assert "filters" in config