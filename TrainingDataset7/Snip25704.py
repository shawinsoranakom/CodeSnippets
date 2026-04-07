def test_emit_no_admins(self):
        handler = AdminEmailHandler()
        record = self.logger.makeRecord(
            "name",
            logging.ERROR,
            "function",
            "lno",
            "message",
            None,
            None,
        )
        with mock.patch.object(
            handler,
            "format_subject",
            side_effect=AssertionError("Should not be called"),
        ):
            handler.emit(record)
        self.assertEqual(len(mail.outbox), 0)