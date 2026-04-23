def test_django_logger_debug(self):
        self.logger.debug("debug")
        self.assertEqual(self.logger_output.getvalue(), "")