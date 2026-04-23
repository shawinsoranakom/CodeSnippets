def test_configure_with_log_rotation(self):
        """Test configure() with log rotation settings."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            log_file_path = Path(tmp_dir) / "test.log"

            # Clear any existing handlers first
            for handler in logging.root.handlers[:]:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    logging.root.removeHandler(handler)

            configure(log_file=log_file_path, log_rotation="50 MB")
            logger = structlog.get_logger()
            assert logger is not None

            # Check that rotating file handler was created with the correct file path
            rotating_handlers = [
                h
                for h in logging.root.handlers
                if isinstance(h, logging.handlers.RotatingFileHandler) and h.baseFilename == str(log_file_path)
            ]
            assert len(rotating_handlers) > 0

            # Check max bytes is set correctly (50 MB = 50 * 1024 * 1024)
            handler = rotating_handlers[0]
            assert handler.maxBytes == 50 * 1024 * 1024

            # Cleanup handlers
            for handler in logging.root.handlers[:]:
                if isinstance(handler, logging.handlers.RotatingFileHandler):
                    logging.root.removeHandler(handler)