def test_deprecated_admins_managers_tuples(self):
        tests = (
            [("nobody", "nobody@example.com"), ("other", "other@example.com")],
            [["nobody", "nobody@example.com"], ["other", "other@example.com"]],
        )
        for setting, mail_func in (
            ("ADMINS", mail_admins),
            ("MANAGERS", mail_managers),
        ):
            msg = (
                f"Using (name, address) pairs in the {setting} setting is deprecated."
                " Replace with a list of email address strings."
            )
            for value in tests:
                self.flush_mailbox()
                with (
                    self.subTest(setting=setting, value=value),
                    self.settings(**{setting: value}),
                ):
                    with self.assertWarnsMessage(RemovedInDjango70Warning, msg):
                        mail_func("subject", "content")
                    message = self.get_the_message()
                    expected_to = ", ".join([str(address) for _, address in value])
                    self.assertEqual(message.get_all("to"), [expected_to])