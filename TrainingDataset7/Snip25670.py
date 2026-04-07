def test_django_logger(self):
        """
        The 'django' base logger only output anything when DEBUG=True.
        """
        self.logger.error("Hey, this is an error.")
        self.assertEqual(self.logger_output.getvalue(), "")

        with self.settings(DEBUG=True):
            self.logger.error("Hey, this is an error.")
            self.assertEqual(self.logger_output.getvalue(), "Hey, this is an error.\n")