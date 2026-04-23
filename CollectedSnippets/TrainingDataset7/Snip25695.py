def test_accepts_args_and_request(self):
        """
        The subject is also handled if being passed a request object.
        """
        message = "Custom message that says '%s' and '%s'"
        token1 = "ping"
        token2 = "pong"

        admin_email_handler = self.get_admin_email_handler(self.logger)
        # Backup then override original filters
        orig_filters = admin_email_handler.filters
        try:
            admin_email_handler.filters = []
            request = self.request_factory.get("/")
            self.logger.error(
                message,
                token1,
                token2,
                extra={
                    "status_code": 403,
                    "request": request,
                },
            )
            self.assertEqual(len(mail.outbox), 1)
            self.assertEqual(mail.outbox[0].to, ["admin@example.com"])
            self.assertEqual(
                mail.outbox[0].subject,
                "-SuperAwesomeSubject-ERROR (internal IP): "
                "Custom message that says 'ping' and 'pong'",
            )
        finally:
            # Restore original filters
            admin_email_handler.filters = orig_filters