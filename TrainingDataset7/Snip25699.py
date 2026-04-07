def test_customize_send_mail_method(self):
        class ManagerEmailHandler(AdminEmailHandler):
            def send_mail(self, subject, message, *args, **kwargs):
                mail.mail_managers(
                    subject, message, *args, connection=self.connection(), **kwargs
                )

        handler = ManagerEmailHandler()
        record = self.logger.makeRecord(
            "name", logging.ERROR, "function", "lno", "message", None, None
        )
        self.assertEqual(len(mail.outbox), 0)
        handler.emit(record)
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, ["manager@example.com"])