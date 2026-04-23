def test_unicode_validator(self):
        valid_usernames = ["joe", "René", "ᴮᴵᴳᴮᴵᴿᴰ", "أحمد"]
        invalid_usernames = [
            "o'connell",
            "عبد ال",
            "zerowidth\u200bspace",
            "nonbreaking\u00a0space",
            "en\u2013dash",
            "trailingnewline\u000a",
        ]
        v = validators.UnicodeUsernameValidator()
        for valid in valid_usernames:
            with self.subTest(valid=valid):
                v(valid)
        for invalid in invalid_usernames:
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValidationError):
                    v(invalid)