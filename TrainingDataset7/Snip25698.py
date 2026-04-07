def test_emit_non_ascii(self):
        """
        #23593 - AdminEmailHandler should allow Unicode characters in the
        request.
        """
        handler = self.get_admin_email_handler(self.logger)
        record = self.logger.makeRecord(
            "name", logging.ERROR, "function", "lno", "message", None, None
        )
        url_path = "/º"
        record.request = self.request_factory.get(url_path)
        handler.emit(record)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.to, ["admin@example.com"])
        self.assertEqual(msg.subject, "[Django] ERROR (EXTERNAL IP): message")
        self.assertIn("Report at %s" % url_path, msg.body)