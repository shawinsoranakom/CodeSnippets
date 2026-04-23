def test_ascii_validator(self):
        valid_usernames = ["glenn", "GLEnN", "jean-marc"]
        invalid_usernames = [
            "o'connell",
            "Éric",
            "jean marc",
            "أحمد",
            "trailingnewline\n",
        ]
        v = validators.ASCIIUsernameValidator()
        for valid in valid_usernames:
            with self.subTest(valid=valid):
                v(valid)
        for invalid in invalid_usernames:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    v(invalid)