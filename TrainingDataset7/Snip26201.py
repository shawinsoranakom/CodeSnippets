def test_wrong_admins_managers(self):
        tests = (
            "test@example.com",
            gettext_lazy("test@example.com"),
            # RemovedInDjango70Warning: uncomment these cases when support for
            # deprecated (name, address) tuples is removed.
            #    [
            #        ("nobody", "nobody@example.com"),
            #        ("other", "other@example.com")
            #    ],
            #    [
            #        ["nobody", "nobody@example.com"],
            #        ["other", "other@example.com"]
            #    ],
            [("name", "test", "example.com")],
            [("Name <test@example.com",)],
            [[]],
        )
        for setting, mail_func in (
            ("ADMINS", mail_admins),
            ("MANAGERS", mail_managers),
        ):
            msg = f"The {setting} setting must be a list of email address strings."
            for value in tests:
                with (
                    self.subTest(setting=setting, value=value),
                    self.settings(**{setting: value}),
                ):
                    with self.assertRaisesMessage(ImproperlyConfigured, msg):
                        mail_func("subject", "content")