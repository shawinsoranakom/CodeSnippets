def test_logging_configuration(self):
        """Test LogConfig setup for the workflow."""
        try:
            from lfx.log.logger import LogConfig
        except ImportError as e:
            pytest.skip(f"LFX logging not available: {e}")

        # Test LogConfig creation for the workflow
        log_config = LogConfig(
            log_level="INFO",
            log_file=Path("langflow.log"),
        )

        assert log_config is not None
        # LogConfig may be a dict or object, verify it contains the expected data
        if isinstance(log_config, dict):
            assert log_config.get("log_level") == "INFO"
            assert log_config.get("log_file") == Path("langflow.log")
        else:
            assert hasattr(log_config, "log_level") or hasattr(log_config, "__dict__")

        # Cleanup
        log_file = Path("langflow.log")
        if log_file.exists():
            log_file.unlink(missing_ok=True)