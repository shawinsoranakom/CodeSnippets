def test_emit_no_form_tag(self):
        """HTML email doesn't contain forms."""
        handler = AdminEmailHandler(include_html=True)
        record = self.logger.makeRecord(
            "name",
            logging.ERROR,
            "function",
            "lno",
            "message",
            None,
            None,
        )
        handler.emit(record)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.subject, "[Django] ERROR: message")
        self.assertEqual(len(msg.alternatives), 1)
        body_html = str(msg.alternatives[0].content)
        self.assertIn('<div id="traceback">', body_html)
        self.assertNotIn("<form", body_html)