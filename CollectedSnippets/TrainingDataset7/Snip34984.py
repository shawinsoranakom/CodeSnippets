def test_log_logger(self):
        logger = logging.getLogger("test.logging")
        cases = [
            (None, "INFO:test.logging:log message"),
            # Test a low custom logging level.
            (5, "Level 5:test.logging:log message"),
            (logging.DEBUG, "DEBUG:test.logging:log message"),
            (logging.INFO, "INFO:test.logging:log message"),
            (logging.WARNING, "WARNING:test.logging:log message"),
            # Test a high custom logging level.
            (45, "Level 45:test.logging:log message"),
        ]
        for level, expected in cases:
            with self.subTest(level=level):
                runner = DiscoverRunner(logger=logger)
                # Pass a logging level smaller than the smallest level in cases
                # in order to capture all messages.
                with self.assertLogs("test.logging", level=1) as cm:
                    runner.log("log message", level)
                self.assertEqual(cm.output, [expected])