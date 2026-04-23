def test_unspecified_password(self):
        """
        Makes sure specifying no plain password with a valid encoded password
        returns `False`.
        """
        self.assertFalse(check_password(None, make_password("lètmein")))