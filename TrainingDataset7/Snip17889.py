def test_check_password_calls_make_password_to_fake_runtime(self):
        cases = [
            (None, None, None),  # no plain text password provided
            ("foo", make_password(password=None), None),  # unusable encoded
            ("letmein", make_password(password="letmein"), ValueError),  # valid encoded
        ]
        for password, encoded, hasher_side_effect in cases:
            with (
                self.subTest(encoded=encoded),
                self.assertMakePasswordCalled(password, encoded, hasher_side_effect),
            ):
                check_password(password, encoded)