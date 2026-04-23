def test_configure_with_invalid_log_rotation(self):
        """Test configure() with invalid log rotation falls back to default."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = Path(tmp_file.name)

        try:
            configure(log_file=log_file_path, log_rotation="invalid rotation")
            config = structlog._config
            assert config is not None

            # Should use default 10MB rotation
            rotating_handlers = [
                h for h in logging.root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
            ]
            if rotating_handlers:
                handler = rotating_handlers[0]
                assert handler.maxBytes == 10 * 1024 * 1024  # Default 10MB
        finally:
            # Cleanup
            if log_file_path.exists():
                log_file_path.unlink()
            for handler in logging.root.handlers[:]:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    logging.root.removeHandler(handler)