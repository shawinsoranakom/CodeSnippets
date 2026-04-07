def test_configure_initializes_logging(self):
        from django import setup

        try:
            with override_settings(
                LOGGING_CONFIG="logging_tests.tests.dictConfig",
            ):
                setup()
        finally:
            # Restore logging from settings.
            setup()
        self.assertTrue(dictConfig.called)