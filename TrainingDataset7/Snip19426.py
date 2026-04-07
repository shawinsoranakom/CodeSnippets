def test_with_referrer_policy(self):
        tests = (
            "strict-origin",
            "strict-origin,origin",
            "strict-origin, origin",
            ["strict-origin", "origin"],
            ("strict-origin", "origin"),
        )
        for value in tests:
            with (
                self.subTest(value=value),
                override_settings(SECURE_REFERRER_POLICY=value),
            ):
                self.assertEqual(base.check_referrer_policy(None), [])