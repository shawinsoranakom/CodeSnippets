def assertEmailMessageSent(self, **kwargs):
        self.assertEqual(len(mail.outbox), 1)
        msg = mail.outbox[0]
        for attr, expected in kwargs.items():
            with self.subTest(attr=attr):
                self.assertEqual(getattr(msg, attr), expected)
        return msg