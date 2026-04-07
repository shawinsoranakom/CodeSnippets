def test_django_logger_info(self):
        self.logger.info("info")
        self.assertEqual(self.logger_output.getvalue(), "info\n")