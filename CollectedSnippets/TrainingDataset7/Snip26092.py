def test_header_injection(self):
        msg = "Header values may not contain linefeed or carriage return characters"
        cases = [
            {"subject": "Subject\nInjection Test"},
            {"subject": gettext_lazy("Lazy Subject\nInjection Test")},
            {"to": ["Name\nInjection test <to@example.com>"]},
        ]
        for kwargs in cases:
            with self.subTest(case=kwargs):
                email = EmailMessage(**kwargs)
                with self.assertRaisesMessage(ValueError, msg):
                    email.message()