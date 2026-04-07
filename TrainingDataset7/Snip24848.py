def test_repeated_nonstandard_keys(self):
        """
        A repeated non-standard name doesn't affect all cookies (#15852).
        """
        self.assertIn("good_cookie", parse_cookie("a:=b; a:=c; good_cookie=yes"))