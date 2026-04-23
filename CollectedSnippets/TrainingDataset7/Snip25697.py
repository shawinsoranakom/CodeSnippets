def test_uses_custom_email_backend(self):
        """
        Refs #19325
        """
        message = "All work and no play makes Jack a dull boy"
        admin_email_handler = self.get_admin_email_handler(self.logger)
        mail_admins_called = {"called": False}

        def my_mail_admins(*args, **kwargs):
            connection = kwargs["connection"]
            self.assertIsInstance(connection, MyEmailBackend)
            mail_admins_called["called"] = True

        # Monkeypatches
        orig_mail_admins = mail.mail_admins
        orig_email_backend = admin_email_handler.email_backend
        mail.mail_admins = my_mail_admins
        admin_email_handler.email_backend = "logging_tests.logconfig.MyEmailBackend"

        try:
            self.logger.error(message)
            self.assertTrue(mail_admins_called["called"])
        finally:
            # Revert Monkeypatches
            mail.mail_admins = orig_mail_admins
            admin_email_handler.email_backend = orig_email_backend