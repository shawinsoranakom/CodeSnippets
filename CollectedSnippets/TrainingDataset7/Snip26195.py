def test_mail_admins_and_managers(self):
        tests = (
            # The ADMINS and MANAGERS settings are lists of email strings.
            ['"Name, Full" <test@example.com>'],
            # Lists and tuples are interchangeable.
            ["test@example.com", "other@example.com"],
            ("test@example.com", "other@example.com"),
            # Lazy strings are supported.
            [gettext_lazy("test@example.com")],
        )
        for setting, mail_func in (
            ("ADMINS", mail_admins),
            ("MANAGERS", mail_managers),
        ):
            for value in tests:
                self.flush_mailbox()
                with (
                    self.subTest(setting=setting, value=value),
                    self.settings(**{setting: value}),
                ):
                    mail_func("subject", "content")
                    message = self.get_the_message()
                    expected_to = ", ".join([str(address) for address in value])
                    self.assertEqual(message.get_all("to"), [expected_to])