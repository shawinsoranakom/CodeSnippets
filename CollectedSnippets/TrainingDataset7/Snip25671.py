def test_django_logger_warning(self):
        self.logger.warning("warning")
        self.assertEqual(self.logger_output.getvalue(), "warning\n")