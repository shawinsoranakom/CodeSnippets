def test_setup_log_formatter(self, messageFormat, config_options):
        """Test streamlit.logger.setup_log_formatter."""

        LOGGER = logger.get_logger("test")

        config._set_option("logger.messageFormat", messageFormat, "test")
        config._set_option("logger.level", logging.DEBUG, "test")

        with patch.object(config, "_config_options", new=config_options):
            logger.setup_formatter(LOGGER)
            self.assertEqual(len(LOGGER.handlers), 1)
            if config_options:
                self.assertEqual(
                    LOGGER.handlers[0].formatter._fmt, messageFormat or "%(message)s"
                )
            else:
                self.assertEqual(
                    LOGGER.handlers[0].formatter._fmt, logger.DEFAULT_LOG_MESSAGE
                )