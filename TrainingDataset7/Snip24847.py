def test_nonstandard_keys(self):
        """
        A single non-standard cookie name doesn't affect all cookies (#13007).
        """
        self.assertIn("good_cookie", parse_cookie("good_cookie=yes;bad:cookie=yes"))