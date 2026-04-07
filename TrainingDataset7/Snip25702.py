def test_custom_exception_reporter_is_used(self):
        record = self.logger.makeRecord(
            "name", logging.ERROR, "function", "lno", "message", None, None
        )
        record.request = self.request_factory.get("/")
        handler = AdminEmailHandler(
            reporter_class="logging_tests.logconfig.CustomExceptionReporter"
        )
        handler.emit(record)
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        self.assertEqual(msg.body, "message\n\ncustom traceback text")