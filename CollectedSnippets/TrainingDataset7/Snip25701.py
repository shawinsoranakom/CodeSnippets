def test_default_exception_reporter_class(self):
        admin_email_handler = self.get_admin_email_handler(self.logger)
        self.assertEqual(admin_email_handler.reporter_class, ExceptionReporter)