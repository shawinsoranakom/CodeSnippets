def test_logging_settings_changed(self):
        """
        Logging is reconfigured when LOGGING or LOGGING_CONFIG changes.
        """
        new_logging_info = {
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {
                "django.test_custom_logger": {
                    "level": "INFO",
                }
            },
        }
        new_logging_warning = {
            "version": 1,
            "disable_existing_loggers": False,
            "loggers": {
                "django.test_custom_logger": {
                    "level": "WARNING",
                }
            },
        }
        logger = logging.getLogger("django.test_custom_logger")

        with override_settings(LOGGING=new_logging_info):
            self.assertEqual(logger.level, logging.INFO)

        # Repeating the operation works.
        with override_settings(LOGGING=new_logging_warning):
            self.assertEqual(logger.level, logging.WARNING)

        # The default unconfigured level is NOTSET.
        self.assertEqual(logger.level, logging.NOTSET)

        self.assertIs(dictConfig.called, False)
        with override_settings(LOGGING_CONFIG="logging_tests.tests.dictConfig"):
            self.assertIs(dictConfig.called, True)