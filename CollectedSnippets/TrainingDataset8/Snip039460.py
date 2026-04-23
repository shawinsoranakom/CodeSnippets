def test_verify_email(self):
        """Test _verify_email."""
        self.assertTrue(_verify_email("user@domain.com").is_valid)
        self.assertTrue(_verify_email("").is_valid)
        self.assertFalse(_verify_email("missing_at_sign").is_valid)