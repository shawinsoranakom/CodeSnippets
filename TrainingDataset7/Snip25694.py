def test_accepts_args(self):
        """
        User-supplied arguments and the EMAIL_SUBJECT_PREFIX setting are used
        to compose the email subject (#16736).
        """
        message = "Custom message that says '%s' and '%s'"
        token1 = "ping"
        token2 = "pong"

        admin_email_handler = self.get_admin_email_handler(self.logger)
        # Backup then override original filters
        orig_filters = admin_email_handler.filters
        try:
            admin_email_handler.filters = []

            self.logger.error(message, token1, token2)

            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
            self.assertEqual(
                mail.outbox[0].subject,
                "-SuperAwesomeSubject-ERROR: "
                "Custom message that says 'ping' and 'pong'",
            )
        finally:
            # Restore original filters
            admin_email_handler.filters = orig_filters