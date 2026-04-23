def test_named_urls(self):
        "Named URLs should be reversible"
        expected_named_urls = [
            ("login", [], {}),
            ("logout", [], {}),
            ("password_change", [], {}),
            ("password_change_done", [], {}),
            ("password_reset", [], {}),
            ("password_reset_done", [], {}),
            (
                "password_reset_confirm",
                [],
                {
                    "uidb64": "aaaaaaa",
                    "token": "1111-aaaaa",
                },
            ),
            ("password_reset_complete", [], {}),
        ]
        for name, args, kwargs in expected_named_urls:
            with self.subTest(name=name):
                try:
                    reverse(name, args=args, kwargs=kwargs)
                except NoReverseMatch:
                    self.fail(
                        "Reversal of url named '%s' failed with NoReverseMatch" % name
                    )