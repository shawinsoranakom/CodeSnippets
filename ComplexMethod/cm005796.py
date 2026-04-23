def test_log_rotation_parsing_edge_cases(self):
        """Test edge cases in log rotation parsing."""
        with tempfile.NamedTemporaryFile(delete=False) as tmp_file:
            log_file_path = Path(tmp_file.name)

        test_cases = [
            ("100 MB", 100 * 1024 * 1024),
            ("50MB", 10 * 1024 * 1024),  # Should fall back to default
            ("invalid format", 10 * 1024 * 1024),  # Should fall back to default
            ("", 10 * 1024 * 1024),  # Should use default
            ("0 MB", 10 * 1024 * 1024),  # Should fall back to default
        ]

        for rotation_str, expected_bytes in test_cases:
            try:
                # Clear any existing handlers
                for handler in logging.root.handlers[:]:
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        logging.root.removeHandler(handler)

                configure(log_file=log_file_path, log_rotation=rotation_str)

                rotating_handlers = [
                    h for h in logging.root.handlers if isinstance(h, logging.handlers.RotatingFileHandler)
                ]

                if rotating_handlers:
                    handler = rotating_handlers[0]
                    assert handler.maxBytes == expected_bytes, f"Failed for rotation '{rotation_str}'"

            finally:
                # Cleanup for each test case
                if log_file_path.exists():
                    with contextlib.suppress(builtins.BaseException):
                        log_file_path.unlink()
                for handler in logging.root.handlers[:]:
                    if isinstance(handler, logging.handlers.RotatingFileHandler):
                        logging.root.removeHandler(handler)